"""An in-memory stand-in for the DoorMonitor panel API v1, just faithful enough for the tests."""

from __future__ import annotations

import re
import uuid
from typing import Any

from aiohttp import web

TOKEN = "a-long-enough-test-token"
ROOT_ID = "root-id"
ROOT_PIN = "1234"
MODES = [
    ("house", "home"),
    ("house", "away"),
    ("house", "vacation"),
    ("party", "halloween"),
    ("party", "christmas"),
    ("party", "easter"),
    ("party", "birthday"),
]


def _user(id: str, name: str, pin: str, level: str) -> dict[str, Any]:
    return {
        "id": id,
        "name": name,
        "pin": pin,
        "start": "2026-01-01T00:00:00Z",
        "end": None,
        "accessLevel": level,
        "bleData": {"phone": None, "watch": None, "misc": None},
        "currentSource": "none",
        "isActive": True,
    }


def _error(status: int, message: str, code: str | None = None) -> web.Response:
    body = {"error": message} | ({"code": code} if code else {})
    return web.json_response(body, status=status)


class FakePanel:
    def __init__(self) -> None:
        self.users = {ROOT_ID: _user(ROOT_ID, "root", ROOT_PIN, "admin")}
        self.modes = {key: {"theme": None, "mediaGroup": None} for key in MODES}
        self.groups = [{"id": "bells", "name": "Bells", "kind": "sound"}]
        self.files: dict[tuple[str, ...], bytes] = {
            ("groups", "bells", "Ding Dong.wav"): b"RIFF" + bytes(range(256)) * 4,
            ("photos", "summer 2.jpg"): b"\xff\xd8\xff" + b"x" * 100,
        }
        #: Every request, as (method, path, actor header).
        self.requests: list[tuple[str, str, str | None]] = []
        self.app = web.Application()
        self.app.router.add_route("*", "/api/v1/{tail:.*}", self.handle)

    async def handle(self, request: web.Request) -> web.StreamResponse:
        actor = request.headers.get("X-Doorbell-Actor")
        self.requests.append((request.method, request.path, actor))
        if request.headers.get("Authorization") != f"Bearer {TOKEN}":
            return _error(401, "Bad API token", "bad-token")
        path = request.match_info["tail"]
        if (request.method, path) == ("GET", "info"):
            return web.json_response(
                {
                    "api": 1,
                    "version": "0.1.25",
                    "features": ["users", "appearance", "media-groups", "photos"],
                    "rootName": "root",
                }
            )
        if (request.method, path) == ("POST", "session"):
            pin = (await request.json()).get("pin")
            admin = next(
                (u for u in self.users.values() if u["pin"] == pin and u["accessLevel"] == "admin"),
                None,
            )
            if admin is None:
                return _error(401, "Wrong PIN, or not an admin", "wrong-pin")
            return web.json_response(admin)
        me = self.users.get(actor or "")
        if me is None or me["accessLevel"] != "admin":
            return _error(401, "Not an admin", "not-admin")
        return await self.route(request, path, me)

    async def route(self, request: web.Request, path: str, me: dict) -> web.StreamResponse:
        method = request.method
        parts = path.split("/")
        if path == "users" and method == "GET":
            return web.json_response(
                sorted(self.users.values(), key=lambda u: u["name"].casefold())
            )
        if path == "users" and method == "POST":
            return self.save_user(await request.json(), None)
        if parts[0] == "users" and len(parts) == 2:
            user_id = parts[1]
            if user_id not in self.users:
                return _error(404, "No such user")
            if method == "GET":
                return web.json_response(self.users[user_id])
            if method == "PUT":
                return self.save_user(await request.json(), user_id)
            if method == "DELETE":
                if user_id == ROOT_ID:
                    return _error(403, "The root user can't be deleted")
                if user_id == me["id"]:
                    return _error(403, "You can't delete your own account")
                del self.users[user_id]
                return web.Response(status=204)
        if path == "appearance" and method == "GET":
            return web.json_response(
                {
                    "modes": [
                        {"key": {"scope": s, "mode": m}, "appearance": self.modes[(s, m)]}
                        for s, m in MODES
                    ],
                    "themes": [{"id": "doorbell", "label": "Doorbell"}],
                    "groups": [{**g, "files": len(self.group_files(g["id"]))} for g in self.groups],
                    "defaultGroup": "bells",
                }
            )
        if parts[0] == "modes" and len(parts) == 3 and method == "PUT":
            key = (parts[1], parts[2])
            if key not in self.modes:
                return _error(404, "That mode has no settings")
            self.modes[key] = await request.json()
            return web.Response(status=204)
        if path == "media" and method == "GET":
            return web.json_response(
                {
                    "photos": [
                        {"name": k[1], "size": len(v), "url": f"media/photos/{k[1]}"}
                        for k, v in self.files.items()
                        if k[0] == "photos"
                    ],
                    "groups": [
                        {
                            **g,
                            "files": [
                                {"name": n, "size": len(self.files[("groups", g["id"], n)])}
                                for n in self.group_files(g["id"])
                            ],
                            "usedBy": [],
                            "isDefault": g["id"] == "bells",
                        }
                        for g in self.groups
                    ],
                }
            )
        if path == "media-groups" and method == "POST":
            body = await request.json()
            if any(g["name"] == body["name"] for g in self.groups):
                return _error(409, "A group with that name already exists")
            group = {"id": uuid.uuid4().hex, "name": body["name"], "kind": body["kind"]}
            self.groups.append(group)
            return web.json_response(group, status=201)
        if parts[0] == "media":
            return await self.media(request, tuple(parts[1:]))
        return _error(404, "Not found")

    def group_files(self, group_id: str) -> list[str]:
        return [k[2] for k in self.files if k[0] == "groups" and k[1] == group_id]

    def save_user(self, body: dict, user_id: str | None) -> web.Response:
        if not str(body.get("name", "")).strip():
            return _error(400, "Name is required")
        if not re.fullmatch(r"\d{4}", str(body.get("pin", ""))):
            return _error(400, "PIN must be 4 digits")
        if any(u["pin"] == body["pin"] and u["id"] != user_id for u in self.users.values()):
            return _error(409, "PIN already in use")
        stored = {**_user(user_id or uuid.uuid4().hex, "", "", ""), **body}
        stored["id"] = user_id or stored["id"]
        stored["name"] = body["name"].strip()
        self.users[stored["id"]] = stored
        return web.json_response(stored, status=200 if user_id else 201)

    async def media(self, request: web.Request, key: tuple[str, ...]) -> web.StreamResponse:
        method = request.method
        if method == "GET":
            if key not in self.files:
                return _error(404, "File not found")
            data = self.files[key]
            if match := re.fullmatch(r"bytes=(\d+)-(\d*)", request.headers.get("Range", "")):
                start = int(match[1])
                end = int(match[2]) if match[2] else len(data) - 1
                return web.Response(
                    status=206,
                    body=data[start : end + 1],
                    headers={
                        "Content-Range": f"bytes {start}-{end}/{len(data)}",
                        "Accept-Ranges": "bytes",
                        "Content-Type": "audio/wav",
                    },
                )
            return web.Response(
                body=data, headers={"Accept-Ranges": "bytes", "Content-Type": "audio/wav"}
            )
        if method == "PUT":
            name = re.sub(r"[^A-Za-z0-9 ._-]", "_", key[-1])
            stored = (*key[:-1], name)
            if stored in self.files and request.query.get("overwrite") != "true":
                return _error(409, f"{name} already exists")
            data = await request.read()
            if not data:
                return _error(400, f"{name} is empty")
            self.files[stored] = data
            return web.json_response({"name": name}, status=201)
        if method == "DELETE":
            if self.files.pop(key, None) is None:
                return _error(404, "File not found")
            return web.Response(status=204)
        return _error(404, "Not found")
