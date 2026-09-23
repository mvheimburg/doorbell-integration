import resolve from "@rollup/plugin-node-resolve";
import commonjs from "@rollup/plugin-commonjs";
import typescript from "@rollup/plugin-typescript";
import terser from "@rollup/plugin-terser";

// One self-contained ES module (lit included), served by the integration.
export default {
  input: "src/doormonitor-admin-panel.ts",
  output: {
    file: "../custom_components/doormonitor/frontend/doormonitor-admin-panel.js",
    format: "es",
    sourcemap: false,
    inlineDynamicImports: true,
  },
  plugins: [
    resolve({ browser: true }),
    commonjs(),
    typescript({ tsconfig: "./tsconfig.build.json" }),
    terser({ format: { comments: false } }),
  ],
};
