const e=globalThis,t=e.ShadowRoot&&(void 0===e.ShadyCSS||e.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,i=Symbol(),s=new WeakMap;let a=class{constructor(e,t,s){if(this._$cssResult$=!0,s!==i)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const i=this.t;if(t&&void 0===e){const t=void 0!==i&&1===i.length;t&&(e=s.get(i)),void 0===e&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),t&&s.set(i,e))}return e}toString(){return this.cssText}};const n=(e,...t)=>{const s=1===e.length?e[0]:t.reduce((t,i,s)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if("number"==typeof e)return e;throw Error("Value passed to 'css' function must be a 'css' function result: "+e+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+e[s+1],e[0]);return new a(s,e,i)},r=t?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t="";for(const i of e.cssRules)t+=i.cssText;return(e=>new a("string"==typeof e?e:e+"",void 0,i))(t)})(e):e,{is:o,defineProperty:d,getOwnPropertyDescriptor:l,getOwnPropertyNames:h,getOwnPropertySymbols:c,getPrototypeOf:p}=Object,u=globalThis,m=u.trustedTypes,g=m?m.emptyScript:"",f=u.reactiveElementPolyfillSupport,v=(e,t)=>e,b={toAttribute(e,t){switch(t){case Boolean:e=e?g:null;break;case Object:case Array:e=null==e?e:JSON.stringify(e)}return e},fromAttribute(e,t){let i=e;switch(t){case Boolean:i=null!==e;break;case Number:i=null===e?null:Number(e);break;case Object:case Array:try{i=JSON.parse(e)}catch(e){i=null}}return i}},$=(e,t)=>!o(e,t),y={attribute:!0,type:String,converter:b,reflect:!1,useDefault:!1,hasChanged:$};Symbol.metadata??=Symbol("metadata"),u.litPropertyMetadata??=new WeakMap;let w=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=y){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){const i=Symbol(),s=this.getPropertyDescriptor(e,i,t);void 0!==s&&d(this.prototype,e,s)}}static getPropertyDescriptor(e,t,i){const{get:s,set:a}=l(this.prototype,e)??{get(){return this[t]},set(e){this[t]=e}};return{get:s,set(t){const n=s?.call(this);a?.call(this,t),this.requestUpdate(e,n,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??y}static _$Ei(){if(this.hasOwnProperty(v("elementProperties")))return;const e=p(this);e.finalize(),void 0!==e.l&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(v("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(v("properties"))){const e=this.properties,t=[...h(e),...c(e)];for(const i of t)this.createProperty(i,e[i])}const e=this[Symbol.metadata];if(null!==e){const t=litPropertyMetadata.get(e);if(void 0!==t)for(const[e,i]of t)this.elementProperties.set(e,i)}this._$Eh=new Map;for(const[e,t]of this.elementProperties){const i=this._$Eu(e,t);void 0!==i&&this._$Eh.set(i,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const i=new Set(e.flat(1/0).reverse());for(const e of i)t.unshift(r(e))}else void 0!==e&&t.push(r(e));return t}static _$Eu(e,t){const i=t.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof e?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),void 0!==this.renderRoot&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){const e=new Map,t=this.constructor.elementProperties;for(const i of t.keys())this.hasOwnProperty(i)&&(e.set(i,this[i]),delete this[i]);e.size>0&&(this._$Ep=e)}createRenderRoot(){const i=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((i,s)=>{if(t)i.adoptedStyleSheets=s.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(const t of s){const s=document.createElement("style"),a=e.litNonce;void 0!==a&&s.setAttribute("nonce",a),s.textContent=t.cssText,i.appendChild(s)}})(i,this.constructor.elementStyles),i}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,i){this._$AK(e,i)}_$ET(e,t){const i=this.constructor.elementProperties.get(e),s=this.constructor._$Eu(e,i);if(void 0!==s&&!0===i.reflect){const a=(void 0!==i.converter?.toAttribute?i.converter:b).toAttribute(t,i.type);this._$Em=e,null==a?this.removeAttribute(s):this.setAttribute(s,a),this._$Em=null}}_$AK(e,t){const i=this.constructor,s=i._$Eh.get(e);if(void 0!==s&&this._$Em!==s){const e=i.getPropertyOptions(s),a="function"==typeof e.converter?{fromAttribute:e.converter}:void 0!==e.converter?.fromAttribute?e.converter:b;this._$Em=s;const n=a.fromAttribute(t,e.type);this[s]=n??this._$Ej?.get(s)??n,this._$Em=null}}requestUpdate(e,t,i,s=!1,a){if(void 0!==e){const n=this.constructor;if(!1===s&&(a=this[e]),i??=n.getPropertyOptions(e),!((i.hasChanged??$)(a,t)||i.useDefault&&i.reflect&&a===this._$Ej?.get(e)&&!this.hasAttribute(n._$Eu(e,i))))return;this.C(e,t,i)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(e,t,{useDefault:i,reflect:s,wrapped:a},n){i&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,n??t??this[e]),!0!==a||void 0!==n)||(this._$AL.has(e)||(this.hasUpdated||i||(t=void 0),this._$AL.set(e,t)),!0===s&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}const e=this.scheduleUpdate();return null!=e&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[e,t]of this._$Ep)this[e]=t;this._$Ep=void 0}const e=this.constructor.elementProperties;if(e.size>0)for(const[t,i]of e){const{wrapped:e}=i,s=this[t];!0!==e||this._$AL.has(t)||void 0===s||this.C(t,void 0,i,s)}}let e=!1;const t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(t){throw e=!1,this._$EM(),t}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(e){}firstUpdated(e){}};w.elementStyles=[],w.shadowRootOptions={mode:"open"},w[v("elementProperties")]=new Map,w[v("finalized")]=new Map,f?.({ReactiveElement:w}),(u.reactiveElementVersions??=[]).push("2.1.2");const k=globalThis,x=e=>e,A=k.trustedTypes,_=A?A.createPolicy("lit-html",{createHTML:e=>e}):void 0,E="$lit$",S=`lit$${Math.random().toFixed(9).slice(2)}$`,U="?"+S,N=`<${U}>`,T=document,M=()=>T.createComment(""),C=e=>null===e||"object"!=typeof e&&"function"!=typeof e,P=Array.isArray,D="[ \t\n\f\r]",B=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,L=/-->/g,H=/>/g,G=RegExp(`>|${D}(?:([^\\s"'>=/]+)(${D}*=${D}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),I=/'/g,O=/"/g,R=/^(?:script|style|textarea|title)$/i,z=e=>(t,...i)=>({_$litType$:e,strings:t,values:i}),j=z(1),V=z(2),F=Symbol.for("lit-noChange"),K=Symbol.for("lit-nothing"),W=new WeakMap,q=T.createTreeWalker(T,129);function J(e,t){if(!P(e)||!e.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==_?_.createHTML(t):t}const Z=(e,t)=>{const i=e.length-1,s=[];let a,n=2===t?"<svg>":3===t?"<math>":"",r=B;for(let t=0;t<i;t++){const i=e[t];let o,d,l=-1,h=0;for(;h<i.length&&(r.lastIndex=h,d=r.exec(i),null!==d);)h=r.lastIndex,r===B?"!--"===d[1]?r=L:void 0!==d[1]?r=H:void 0!==d[2]?(R.test(d[2])&&(a=RegExp("</"+d[2],"g")),r=G):void 0!==d[3]&&(r=G):r===G?">"===d[0]?(r=a??B,l=-1):void 0===d[1]?l=-2:(l=r.lastIndex-d[2].length,o=d[1],r=void 0===d[3]?G:'"'===d[3]?O:I):r===O||r===I?r=G:r===L||r===H?r=B:(r=G,a=void 0);const c=r===G&&e[t+1].startsWith("/>")?" ":"";n+=r===B?i+N:l>=0?(s.push(o),i.slice(0,l)+E+i.slice(l)+S+c):i+S+(-2===l?t:c)}return[J(e,n+(e[i]||"<?>")+(2===t?"</svg>":3===t?"</math>":"")),s]};class X{constructor({strings:e,_$litType$:t},i){let s;this.parts=[];let a=0,n=0;const r=e.length-1,o=this.parts,[d,l]=Z(e,t);if(this.el=X.createElement(d,i),q.currentNode=this.el.content,2===t||3===t){const e=this.el.content.firstChild;e.replaceWith(...e.childNodes)}for(;null!==(s=q.nextNode())&&o.length<r;){if(1===s.nodeType){if(s.hasAttributes())for(const e of s.getAttributeNames())if(e.endsWith(E)){const t=l[n++],i=s.getAttribute(e).split(S),r=/([.?@])?(.*)/.exec(t);o.push({type:1,index:a,name:r[2],strings:i,ctor:"."===r[1]?ie:"?"===r[1]?se:"@"===r[1]?ae:te}),s.removeAttribute(e)}else e.startsWith(S)&&(o.push({type:6,index:a}),s.removeAttribute(e));if(R.test(s.tagName)){const e=s.textContent.split(S),t=e.length-1;if(t>0){s.textContent=A?A.emptyScript:"";for(let i=0;i<t;i++)s.append(e[i],M()),q.nextNode(),o.push({type:2,index:++a});s.append(e[t],M())}}}else if(8===s.nodeType)if(s.data===U)o.push({type:2,index:a});else{let e=-1;for(;-1!==(e=s.data.indexOf(S,e+1));)o.push({type:7,index:a}),e+=S.length-1}a++}}static createElement(e,t){const i=T.createElement("template");return i.innerHTML=e,i}}function Y(e,t,i=e,s){if(t===F)return t;let a=void 0!==s?i._$Co?.[s]:i._$Cl;const n=C(t)?void 0:t._$litDirective$;return a?.constructor!==n&&(a?._$AO?.(!1),void 0===n?a=void 0:(a=new n(e),a._$AT(e,i,s)),void 0!==s?(i._$Co??=[])[s]=a:i._$Cl=a),void 0!==a&&(t=Y(e,a._$AS(e,t.values),a,s)),t}class Q{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){const{el:{content:t},parts:i}=this._$AD,s=(e?.creationScope??T).importNode(t,!0);q.currentNode=s;let a=q.nextNode(),n=0,r=0,o=i[0];for(;void 0!==o;){if(n===o.index){let t;2===o.type?t=new ee(a,a.nextSibling,this,e):1===o.type?t=new o.ctor(a,o.name,o.strings,this,e):6===o.type&&(t=new ne(a,this,e)),this._$AV.push(t),o=i[++r]}n!==o?.index&&(a=q.nextNode(),n++)}return q.currentNode=T,s}p(e){let t=0;for(const i of this._$AV)void 0!==i&&(void 0!==i.strings?(i._$AI(e,i,t),t+=i.strings.length-2):i._$AI(e[t])),t++}}class ee{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,i,s){this.type=2,this._$AH=K,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=i,this.options=s,this._$Cv=s?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode;const t=this._$AM;return void 0!==t&&11===e?.nodeType&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=Y(this,e,t),C(e)?e===K||null==e||""===e?(this._$AH!==K&&this._$AR(),this._$AH=K):e!==this._$AH&&e!==F&&this._(e):void 0!==e._$litType$?this.$(e):void 0!==e.nodeType?this.T(e):(e=>P(e)||"function"==typeof e?.[Symbol.iterator])(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==K&&C(this._$AH)?this._$AA.nextSibling.data=e:this.T(T.createTextNode(e)),this._$AH=e}$(e){const{values:t,_$litType$:i}=e,s="number"==typeof i?this._$AC(e):(void 0===i.el&&(i.el=X.createElement(J(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===s)this._$AH.p(t);else{const e=new Q(s,this),i=e.u(this.options);e.p(t),this.T(i),this._$AH=e}}_$AC(e){let t=W.get(e.strings);return void 0===t&&W.set(e.strings,t=new X(e)),t}k(e){P(this._$AH)||(this._$AH=[],this._$AR());const t=this._$AH;let i,s=0;for(const a of e)s===t.length?t.push(i=new ee(this.O(M()),this.O(M()),this,this.options)):i=t[s],i._$AI(a),s++;s<t.length&&(this._$AR(i&&i._$AB.nextSibling,s),t.length=s)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){const t=x(e).nextSibling;x(e).remove(),e=t}}setConnected(e){void 0===this._$AM&&(this._$Cv=e,this._$AP?.(e))}}class te{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,i,s,a){this.type=1,this._$AH=K,this._$AN=void 0,this.element=e,this.name=t,this._$AM=s,this.options=a,i.length>2||""!==i[0]||""!==i[1]?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=K}_$AI(e,t=this,i,s){const a=this.strings;let n=!1;if(void 0===a)e=Y(this,e,t,0),n=!C(e)||e!==this._$AH&&e!==F,n&&(this._$AH=e);else{const s=e;let r,o;for(e=a[0],r=0;r<a.length-1;r++)o=Y(this,s[i+r],t,r),o===F&&(o=this._$AH[r]),n||=!C(o)||o!==this._$AH[r],o===K?e=K:e!==K&&(e+=(o??"")+a[r+1]),this._$AH[r]=o}n&&!s&&this.j(e)}j(e){e===K?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}}class ie extends te{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===K?void 0:e}}class se extends te{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==K)}}class ae extends te{constructor(e,t,i,s,a){super(e,t,i,s,a),this.type=5}_$AI(e,t=this){if((e=Y(this,e,t,0)??K)===F)return;const i=this._$AH,s=e===K&&i!==K||e.capture!==i.capture||e.once!==i.once||e.passive!==i.passive,a=e!==K&&(i===K||s);s&&this.element.removeEventListener(this.name,this,i),a&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}}class ne{constructor(e,t,i){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(e){Y(this,e)}}const re=k.litHtmlPolyfillSupport;re?.(X,ee),(k.litHtmlVersions??=[]).push("3.3.3");const oe=globalThis;class de extends w{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){const t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=((e,t,i)=>{const s=i?.renderBefore??t;let a=s._$litPart$;if(void 0===a){const e=i?.renderBefore??null;s._$litPart$=a=new ee(t.insertBefore(M(),e),e,void 0,i??{})}return a._$AI(e),a})(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return F}}de._$litElement$=!0,de.finalized=!0,oe.litElementHydrateSupport?.({LitElement:de});const le=oe.litElementPolyfillSupport;le?.({LitElement:de}),(oe.litElementVersions??=[]).push("4.2.2");const he=new Set(["not-admin","bad-token","not-configured"]);class ce extends Error{constructor(e,t){super(e),this.code=t}}const pe=e=>e instanceof ce?e:new ce(e?.message||String(e),e?.code||"unknown");class ue{constructor(e,t){this.hass=e,this.entryId=t}async ws(e){try{return await this.hass.callWS({entry_id:this.entryId,...e})}catch(e){throw pe(e)}}call(e,t,i){return this.ws({type:"doormonitor/admin/call",method:e,path:t,...void 0===i?{}:{body:i}})}users(){return this.ws({type:"doormonitor/admin/users"})}saveUser(e,t,i){return this.ws({type:"doormonitor/admin/save_user",...e?{user_id:e}:{},user:t,ha_user_id:i})}mediaUrl(e){return`/api/doormonitor/${this.entryId}/media/${e.map(encodeURIComponent).join("/")}`}async signedUrl(e){return(await this.hass.callWS({type:"auth/sign_path",path:this.mediaUrl(e),expires:3600})).path}async upload(e,t,i){let s;try{s=await this.hass.fetchWithAuth(this.mediaUrl(e)+(i?"?overwrite=true":""),{method:"PUT",body:t,headers:{"Content-Type":t.type||"application/octet-stream"}})}catch{throw new ce("The panel is unreachable","unreachable")}const a=await s.json().catch(()=>null);if(!s.ok)throw new ce(a?.error||`HTTP ${s.status}`,a?.code||`http-${s.status}`);return a?.name??t.name}}const me={bell:V`<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"></path><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"></path>`,users:V`<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"></path>`,userPlus:V`<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M19 8v6M22 11h-6"></path>`,home:V`<path d="M3 10.5 12 3l9 7.5"></path><path d="M5 9.5V21h14V9.5"></path>`,party:V`<path d="M5.8 11.3 2 22l10.7-3.8"></path><path d="M4 3h.01M22 8h.01M15 2h.01M22 20h.01"></path><path d="m22 2-2.24.75a2.9 2.9 0 0 0-1.96 3.12c.1.86-.57 1.63-1.45 1.63h-.38c-.86 0-1.6.6-1.76 1.44L14 10"></path><path d="m22 13-.82-.33c-.86-.34-1.82.2-1.98 1.11-.11.7-.72 1.22-1.43 1.22H17"></path><path d="m11 2 .33.82c.34.86-.2 1.82-1.11 1.98-.7.1-1.22.72-1.22 1.43V7"></path><path d="M11 13c1.93 1.93 2.83 4.17 2 5-.83.83-3.07-.07-5-2-1.93-1.93-2.83-4.17-2-5 .83-.83 3.07.07 5 2z"></path>`,folderPlus:V`<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2z"></path><path d="M12 10v6M9 13h6"></path>`,music:V`<path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle>`,film:V`<rect x="2" y="2" width="20" height="20" rx="2.18"></rect><path d="M7 2v20M17 2v20M2 12h20M2 7h5M2 17h5M17 17h5M17 7h5"></path>`,image:V`<rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="9" cy="9" r="2"></circle><path d="m21 15-3.09-3.09a2 2 0 0 0-2.82 0L6 21"></path>`,pencil:V`<path d="M17 3a2.85 2.85 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5z"></path>`,trash:V`<path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M10 11v6M14 11v6"></path>`,check:V`<path d="M20 6 9 17l-5-5"></path>`,close:V`<path d="M18 6 6 18M6 6l12 12"></path>`,plus:V`<path d="M12 5v14M5 12h14"></path>`,upload:V`<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><path d="m17 8-5-5-5 5M12 3v12"></path>`,spinner:V`<path d="M21 12a9 9 0 1 1-6.2-8.56"></path>`,warning:V`<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"></path><path d="M12 9v4M12 17h.01"></path>`,cog:V`<circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path>`,menu:V`<path d="M4 6h16M4 12h16M4 18h16"></path>`,link:V`<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>`};function ge(e,t=""){return j`<svg
    class="i ${t}"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    ${me[e]}
  </svg>`}const fe={title:"Doorbell",menu:"Open the sidebar",entry:"Doorbell panel",actingAs:"Acting as {name}",settings:"DoorMonitor settings",loading:"Loading…",couldNotLoad:"Couldn't load: {message}",retry:"Retry",noFeatures:"This panel offers nothing this admin app can manage.",notSetUpTitle:"No doorbell connected",notSetUpBody:"Add DoorMonitor under Settings → Devices & services and pick your doorbell panel. Its users, appearance and media can be managed here afterwards.",notConfiguredTitle:"Admin connection not set up",notConfiguredBody:"To manage the doorbell from here, open DoorMonitor's Configure → Admin connection and enter the panel API's address, its token and an admin PIN.",notAdminTitle:"The doorbell admin is gone",notAdminBody:"The doorbell admin this integration acts as ({name}) was deleted, demoted or deactivated. Enter an admin PIN again under Configure → Admin connection.",badTokenTitle:"The token was refused",badTokenBody:"The integration can't talk to the panel (API token). Check the token under Configure → Admin connection.",openSettings:"Open DoorMonitor settings",tabs:{users:"Users",appearance:"Appearance","media-groups":"Sounds & videos",photos:"Photos"},errors:{unreachable:"The panel is unreachable","bad-response":"The panel sent an answer this app doesn't understand","tls-failed":"Home Assistant did not accept the panel's certificate. Check the certificate verification setting under Configure → Admin connection.","fingerprint-mismatch":"The panel's certificate has changed and no longer matches the pinned fingerprint. Verify it on the server before updating the fingerprint under Configure → Admin connection.",unauthorized:"The panel API refused the authentication",forbidden:"Access was denied. Check the reverse proxy's IP allowlist and the panel's authorization.",redirect:"The panel address answered with a redirect, which is not followed. Enter the final address under Configure → Admin connection.","ha-user-linked":"That Home Assistant user is already linked to another doorbell user","unknown-ha-user":"That Home Assistant user no longer exists"},saved:"✅ Saved",savedName:"✅ Saved {name}",deletedName:"🗑️ Deleted {name}",createdName:"✅ Created {name}",renamedTo:"✅ Renamed to {name}",uploaded:"✅ Uploaded {names}",failed:"❌ {message}",failedAfter:"❌ {message} (uploaded before it: {names})",users:"Users",addUser:"Add User",editUser:"Edit User",editName:"Edit {name}",deleteName:"Delete {name}",access:{admin:"admin",resident:"resident",guest:"guest"},accessOption:{guest:"Guest",resident:"Resident",admin:"Admin"},inactive:"Not active now",linkedTo:"Home Assistant: {name}",haUser:"Home Assistant user",haUserNone:"None",haUserHint:"Picking a person fills in the name and links this doorbell user to them.",name:"Name",pin:"PIN (4 digits)",accessLevel:"Access level",activeFrom:"Active from",activeUntil:"Active until (optional)",ble:{phone:"BLE phone",watch:"BLE watch",misc:"BLE misc"},bleKind:{ibeacon:"iBeacon",mac:"MAC",uuid:"UUID"},bleKindLabel:"{slot} kind",save:"Save",cancel:"Cancel",delete:"Delete",deleteTitle:"Delete {name}?",cannotUndo:"This cannot be undone.",appearanceIntro:"A party mode's choices win over the house mode while the party mode is on. Groups of sounds and videos are managed on the Sounds & videos tab. Changes show on the doorbell within a second.",modes:{home:"Home",away:"Away",vacation:"Vacation",halloween:"Halloween",christmas:"Christmas",easter:"Easter",birthday:"Birthday"},theme:"Theme",themeDefault:"Doorbell (default)",sameAsHouse:"Same as house mode",bellMedia:"Bell sounds or videos",defaultGroup:"Default: {name}",defaultNone:"Default: none",groupSounds:"{name} · {n} sounds",groupSound:"{name} · 1 sound",groupVideos:"{name} · {n} videos",groupVideo:"{name} · 1 video",hintEmpty:"This group is empty, so the doorbell plays its built-in bell.",hintVideo:"Plays a random video, with only the video's own sound.",hintSound:"Plays a random sound from the group.",hintParty:"Uses the house mode's group.",hintDefault:"Uses the oldest sound group.",hintNone:"Create a sound group on the Sounds & videos tab.",saving:"Saving…",newGroup:"New group",newGroupIntro:"A group holds bell sounds or videos. Each mode picks a group on the Appearance tab, and a bell press plays a random file from it. Videos play with their own sound only.",groupNamePlaceholder:"Name, for example Spooky",groupName:"Group name",kind:"Kind",kindSounds:"Sounds",kindVideos:"Videos",create:"Create",noGroups:"No groups yet, so the doorbell plays its built-in bell.",renameGroup:"Rename group",deleteGroup:"Delete group",defaultBadge:"Default",usedAndDefault:"Used by {modes}, and by modes without a group of their own.",used:"Used by {modes}.",defaultOnly:"Played by modes without a group of their own.",unused:"No mode uses this group yet.",noSounds:"No sounds yet.",noVideos:"No videos yet.",deleteGroupEmpty:"Deletes the empty group.",deleteGroupOne:"Deletes the group and its 1 file.",deleteGroupMany:"Deletes the group and its {n} files.",modesFallBack:"{modes} will use their default again.",rename:"Rename {name}",saveName:"Save name",newName:"New name",replace:"Replace files with the same name",chooseFiles:"Files to upload",upload:"Upload",sizeNote:"Up to {n} MB per file.",photosTitle:"Family photos",photosIntro:"The doorbell's home screen shows these in turn.",noPhotos:"No photos yet.",close:"Close"},ve={title:"Ringeklokke",menu:"Åpne sidepanelet",entry:"Ringeklokkepanel",actingAs:"Handler som {name}",settings:"DoorMonitor-innstillinger",loading:"Laster …",couldNotLoad:"Kunne ikke laste: {message}",retry:"Prøv igjen",noFeatures:"Dette panelet tilbyr ingenting denne administrasjonen kan styre.",notSetUpTitle:"Ingen ringeklokke er koblet til",notSetUpBody:"Legg til DoorMonitor under Innstillinger → Enheter og tjenester og velg ringeklokkepanelet. Brukere, utseende og medier kan deretter styres her.",notConfiguredTitle:"Administratortilkoblingen er ikke satt opp",notConfiguredBody:"For å styre ringeklokken herfra åpner du Konfigurer → Administratortilkobling for DoorMonitor og skriver inn adressen til panel-API-et, tokenet og en administrator-PIN.",notAdminTitle:"Ringeklokke-administratoren finnes ikke lenger",notAdminBody:"Administratoren denne integrasjonen handler som ({name}), er slettet, nedgradert eller deaktivert. Skriv inn en administrator-PIN på nytt under Konfigurer → Administratortilkobling.",badTokenTitle:"Tokenet ble avvist",badTokenBody:"Integrasjonen får ikke snakke med panelet (API-token). Sjekk tokenet under Konfigurer → Administratortilkobling.",openSettings:"Åpne DoorMonitor-innstillingene",tabs:{users:"Brukere",appearance:"Utseende","media-groups":"Lyder og videoer",photos:"Bilder"},errors:{unreachable:"Får ikke kontakt med panelet","bad-response":"Panelet sendte et svar denne appen ikke forstår","tls-failed":"Home Assistant godtok ikke panelets sertifikat. Sjekk sertifikatkontrollen under Konfigurer → Administratortilkobling.","fingerprint-mismatch":"Panelets sertifikat er endret og stemmer ikke lenger med det festede fingeravtrykket. Kontroller det på serveren før du oppdaterer fingeravtrykket under Konfigurer → Administratortilkobling.",unauthorized:"Panel-API-et avviste autentiseringen",forbidden:"Tilgang nektet. Sjekk IP-tillatelseslisten i den omvendte proxyen og panelets tilgangskontroll.",redirect:"Paneladressen svarte med en videresending, som ikke følges. Skriv inn den endelige adressen under Konfigurer → Administratortilkobling.","ha-user-linked":"Denne Home Assistant-brukeren er allerede koblet til en annen ringeklokkebruker","unknown-ha-user":"Denne Home Assistant-brukeren finnes ikke lenger"},saved:"✅ Lagret",savedName:"✅ Lagret {name}",deletedName:"🗑️ Slettet {name}",createdName:"✅ Opprettet {name}",renamedTo:"✅ Omdøpt til {name}",uploaded:"✅ Lastet opp {names}",failed:"❌ {message}",failedAfter:"❌ {message} (lastet opp før dette: {names})",users:"Brukere",addUser:"Legg til bruker",editUser:"Rediger bruker",editName:"Rediger {name}",deleteName:"Slett {name}",access:{admin:"administrator",resident:"beboer",guest:"gjest"},accessOption:{guest:"Gjest",resident:"Beboer",admin:"Administrator"},inactive:"Ikke aktiv nå",linkedTo:"Home Assistant: {name}",haUser:"Home Assistant-bruker",haUserNone:"Ingen",haUserHint:"Velger du en person, fylles navnet inn og ringeklokkebrukeren kobles til personen.",name:"Navn",pin:"PIN (4 sifre)",accessLevel:"Tilgangsnivå",activeFrom:"Aktiv fra",activeUntil:"Aktiv til (valgfritt)",ble:{phone:"BLE telefon",watch:"BLE klokke",misc:"BLE annet"},bleKind:{ibeacon:"iBeacon",mac:"MAC",uuid:"UUID"},bleKindLabel:"Type for {slot}",save:"Lagre",cancel:"Avbryt",delete:"Slett",deleteTitle:"Slette {name}?",cannotUndo:"Dette kan ikke angres.",appearanceIntro:"Valgene for en festmodus vinner over husmodusen mens festmodusen er på. Grupper med lyder og videoer styres på fanen Lyder og videoer. Endringer vises på ringeklokken innen et sekund.",modes:{home:"Hjemme",away:"Borte",vacation:"Ferie",halloween:"Halloween",christmas:"Jul",easter:"Påske",birthday:"Bursdag"},theme:"Tema",themeDefault:"Doorbell (standard)",sameAsHouse:"Samme som husmodus",bellMedia:"Ringelyder eller videoer",defaultGroup:"Standard: {name}",defaultNone:"Standard: ingen",groupSounds:"{name} · {n} lyder",groupSound:"{name} · 1 lyd",groupVideos:"{name} · {n} videoer",groupVideo:"{name} · 1 video",hintEmpty:"Denne gruppen er tom, så ringeklokken spiller den innebygde ringelyden.",hintVideo:"Spiller en tilfeldig video, bare med videoens egen lyd.",hintSound:"Spiller en tilfeldig lyd fra gruppen.",hintParty:"Bruker gruppen til husmodusen.",hintDefault:"Bruker den eldste lydgruppen.",hintNone:"Lag en lydgruppe på fanen Lyder og videoer.",saving:"Lagrer …",newGroup:"Ny gruppe",newGroupIntro:"En gruppe inneholder ringelyder eller videoer. Hver modus velger en gruppe på fanen Utseende, og et trykk på ringeklokken spiller en tilfeldig fil fra den. Videoer spilles bare med sin egen lyd.",groupNamePlaceholder:"Navn, for eksempel Skummelt",groupName:"Gruppenavn",kind:"Type",kindSounds:"Lyder",kindVideos:"Videoer",create:"Opprett",noGroups:"Ingen grupper ennå, så ringeklokken spiller den innebygde ringelyden.",renameGroup:"Gi gruppen nytt navn",deleteGroup:"Slett gruppen",defaultBadge:"Standard",usedAndDefault:"Brukes av {modes}, og av moduser uten egen gruppe.",used:"Brukes av {modes}.",defaultOnly:"Spilles av moduser uten egen gruppe.",unused:"Ingen modus bruker denne gruppen ennå.",noSounds:"Ingen lyder ennå.",noVideos:"Ingen videoer ennå.",deleteGroupEmpty:"Sletter den tomme gruppen.",deleteGroupOne:"Sletter gruppen og den ene filen i den.",deleteGroupMany:"Sletter gruppen og de {n} filene i den.",modesFallBack:"{modes} bruker standardvalget sitt igjen.",rename:"Gi {name} nytt navn",saveName:"Lagre navnet",newName:"Nytt navn",replace:"Erstatt filer med samme navn",chooseFiles:"Filer som skal lastes opp",upload:"Last opp",sizeNote:"Opptil {n} MB per fil.",photosTitle:"Familiebilder",photosIntro:"Startskjermen på ringeklokken viser disse etter tur.",noPhotos:"Ingen bilder ennå.",close:"Lukk"};function be(e){return"nb"===function(e){const t=String(e?.language||e?.locale?.language||"en").toLowerCase().replace(/_/g,"-");return/^(nb|no|nn)(-|$)/.test(t)?"nb":"en"}(e)?ve:fe}function $e(e,t){return e.replace(/\{(\w+)\}/g,(e,i)=>String(t[i]??""))}function ye(e,t){return e.modes[t.mode]??t.mode}function we(e,t){return t.code&&e.errors[t.code]||t.message}const ke=n`
  :host {
    display: block;
    box-sizing: border-box;
    color: var(--primary-text-color);
    font-family: var(
      --ha-font-family-body,
      var(--paper-font-body1_-_font-family, inherit)
    );
    -webkit-font-smoothing: antialiased;
    --dm-text: var(--primary-text-color, #1b1b1a);
    --dm-muted: var(--secondary-text-color, #5b5a55);
    --dm-accent: var(--primary-color, #03a9f4);
    --dm-on-accent: var(--text-primary-color, #fff);
    --dm-error: var(--error-color, #c62828);
    --dm-success: var(--success-color, #2e7d32);
    --dm-warning: var(--warning-color, #f59e0b);
    --dm-info: var(--info-color, #039be5);
    --dm-surface: var(--ha-card-background, var(--card-background-color, #fff));
    --dm-pill: var(--secondary-background-color, #f3f2ee);
    --dm-line: var(--divider-color, rgba(0, 0, 0, 0.12));
    --dm-radius: var(--ha-card-border-radius, 12px);
  }
  * {
    box-sizing: border-box;
  }
  [hidden] {
    display: none !important;
  }
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
  }
  .i {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
  }
  .i.s {
    width: 16px;
    height: 16px;
  }
  .spin {
    animation: spin 0.9s linear infinite;
  }
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
  .card {
    background: var(--dm-surface);
    border: 1px solid var(--dm-line);
    border-radius: var(--dm-radius);
    box-shadow: var(--ha-card-box-shadow, none);
    padding: 20px 24px;
  }
  .card + .card {
    margin-top: 16px;
  }
  .card-head {
    display: flex;
    align-items: center;
    gap: 10px;
    min-height: 40px;
    flex-wrap: wrap;
  }
  .card-head h2 {
    margin: 0;
    font-size: 1.2rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    flex: 1;
  }
  .card-head h2 span {
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .card-head .tools {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-left: auto;
  }
  .intro,
  .muted {
    color: var(--dm-muted);
  }
  .intro {
    margin: 8px 0 12px;
    line-height: 1.45;
  }
  .note,
  .hint {
    color: var(--dm-muted);
    font-size: 0.8rem;
    margin: 6px 0 0;
  }
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    min-height: 40px;
    padding: 0 16px;
    border-radius: 8px;
    border: 1px solid var(--dm-line);
    background: transparent;
    color: var(--dm-text);
    font: inherit;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }
  .btn.primary {
    background: var(--dm-accent);
    border-color: var(--dm-accent);
    color: var(--dm-on-accent);
  }
  .btn.danger {
    background: var(--dm-error);
    border-color: var(--dm-error);
    color: #fff;
  }
  .btn:disabled {
    opacity: 0.45;
    cursor: default;
  }
  .icon-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: none;
    background: transparent;
    color: var(--dm-text);
    cursor: pointer;
    flex-shrink: 0;
  }
  .icon-btn:hover:not(:disabled) {
    background: var(--dm-pill);
  }
  .icon-btn.danger {
    color: var(--dm-error);
  }
  .icon-btn:disabled {
    opacity: 0.4;
    cursor: default;
  }
  .icon-btn.spacer {
    visibility: hidden;
  }
  .btn:focus-visible,
  .icon-btn:focus-visible,
  input:focus-visible,
  select:focus-visible {
    outline: 2px solid var(--dm-accent);
    outline-offset: 2px;
  }
  .badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.85rem;
    background: var(--dm-pill);
    color: var(--dm-text);
    white-space: nowrap;
  }
  .badge.admin {
    background: color-mix(in srgb, var(--dm-info) 25%, transparent);
  }
  .badge.resident {
    background: color-mix(in srgb, var(--dm-warning) 30%, transparent);
  }
  .badge.guest {
    background: color-mix(in srgb, var(--dm-success) 25%, transparent);
  }
  .badge.default {
    background: color-mix(in srgb, var(--dm-accent) 22%, transparent);
  }
  label.field {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    min-width: 0;
  }
  input[type="text"],
  input[type="password"],
  input[type="date"],
  select {
    font: inherit;
    font-weight: 400;
    color: var(--dm-text);
    background: var(--dm-surface);
    border: 1px solid var(--dm-line);
    border-radius: 8px;
    min-height: 40px;
    padding: 0 12px;
    width: 100%;
    min-width: 0;
  }
  input[type="date"] {
    color-scheme: light dark;
  }
  input[type="checkbox"] {
    width: 20px;
    height: 20px;
    accent-color: var(--dm-accent);
  }
  .alert {
    display: flex;
    gap: 10px;
    align-items: flex-start;
    padding: 12px 14px;
    border-radius: 8px;
    background: color-mix(in srgb, var(--dm-error) 14%, transparent);
    color: var(--dm-text);
    margin: 8px 0;
  }
  .alert .i {
    color: var(--dm-error);
  }
  .alert .grow {
    flex: 1;
  }
  .center {
    display: flex;
    justify-content: center;
    padding: 48px 0;
    color: var(--dm-muted);
  }
  .center .i {
    width: 32px;
    height: 32px;
  }
  /* Rows */
  .rows {
    list-style: none;
    margin: 8px 0 0;
    padding: 0;
  }
  .row {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 48px;
    padding: 4px 0;
    border-top: 1px solid var(--dm-line);
  }
  .row:first-child {
    border-top: none;
  }
  .row.inactive .who {
    opacity: 0.5;
  }
  .who {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
  }
  .who .name {
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .who .sub {
    font-size: 0.8rem;
    color: var(--dm-muted);
    display: flex;
    gap: 4px;
    align-items: center;
  }
  /* Files */
  .file-row {
    display: flex;
    align-items: center;
    gap: 4px;
    min-width: 0;
  }
  .file-row .fname {
    flex: 1;
    min-width: 0;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .file-row .size {
    color: var(--dm-muted);
    font-size: 0.8rem;
    margin-right: 4px;
    white-space: nowrap;
  }
  .sound {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 6px 0;
    flex-wrap: wrap;
  }
  .sound .file-row {
    flex: 1 1 240px;
  }
  .sound audio {
    flex: 1 1 260px;
    min-width: 0;
    height: 40px;
  }
  .grid {
    display: grid;
    gap: 16px;
    margin-top: 8px;
  }
  .grid.videos {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .grid.photos {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
  video {
    width: 100%;
    aspect-ratio: 16 / 9;
    background: #000;
    border-radius: 8px;
    display: block;
  }
  .photo img {
    width: 100%;
    aspect-ratio: 1;
    object-fit: cover;
    border-radius: 8px;
    display: block;
    background: var(--dm-pill);
  }
  .rename {
    display: flex;
    align-items: center;
    gap: 4px;
    flex: 1;
    min-width: 0;
  }
  .rename input {
    flex: 1;
  }
  .rename .ext {
    color: var(--dm-muted);
  }
  .upload {
    border-top: 1px solid var(--dm-line);
    margin-top: 16px;
    padding-top: 16px;
  }
  .upload .line {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
  }
  .upload .check {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--dm-muted);
  }
  .upload input[type="file"] {
    flex: 1 1 220px;
    min-width: 0;
    font: inherit;
    color: var(--dm-muted);
  }
  .inline-form {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  .inline-form input {
    flex: 1 1 220px;
  }
  .inline-form select {
    width: auto;
  }
  /* Appearance */
  .modes {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
  }
  .modes .card + .card {
    margin-top: 0;
  }
  .mode label.field + label.field {
    margin-top: 16px;
  }
  /* Dialogs */
  .scrim {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
    z-index: 10;
  }
  .dialog {
    background: var(--dm-surface);
    color: var(--dm-text);
    border-radius: var(--dm-radius);
    width: min(560px, 100%);
    max-height: calc(100vh - 32px);
    overflow: auto;
    padding: 20px 24px;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
  }
  .dialog h2 {
    margin: 0 0 12px;
    font-size: 1.2rem;
  }
  .dialog p {
    margin: 6px 0;
    line-height: 1.45;
  }
  .form {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
  }
  .form .wide {
    grid-column: 1 / -1;
  }
  .ble {
    display: grid;
    grid-template-columns: 120px minmax(0, 1fr);
    gap: 8px;
  }
  .dialog-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 20px;
  }
  @media (max-width: 700px) {
    .card {
      padding: 16px;
    }
    .modes,
    .form,
    .grid.videos {
      grid-template-columns: minmax(0, 1fr);
    }
    .grid.photos {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }
  @media (min-width: 701px) and (max-width: 960px) {
    .grid.photos {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }
`,xe=1048576;function Ae(e){return e?e.slice(0,10):""}function _e(e){return`${e}T00:00:00Z`}function Ee(e=new Date){const t=e=>String(e).padStart(2,"0");return`${e.getFullYear()}-${t(e.getMonth()+1)}-${t(e.getDate())}`}class Se extends de{constructor(){super(...arguments),this.value="",this.suffix="",this.maxLength=100,this.busy=!1,this.label="",this.text=""}willUpdate(e){e.has("value")&&(this.text=this.value)}firstUpdated(){const e=this.renderRoot.querySelector("input");e?.focus(),e?.select()}save(){const e=this.text.trim();e&&!this.busy&&this.dispatchEvent(new CustomEvent("dm-save",{detail:e}))}render(){const e=this.t;return j`<div class="rename">
      <input
        type="text"
        aria-label=${this.label||e.newName}
        maxlength=${this.maxLength}
        .value=${this.text}
        ?disabled=${this.busy}
        @input=${e=>this.text=e.target.value}
        @keydown=${e=>{"Enter"===e.key&&this.save(),"Escape"===e.key&&this.dispatchEvent(new CustomEvent("dm-cancel"))}}
      />
      ${this.suffix?j`<span class="ext">${this.suffix}</span>`:K}
      <button
        class="icon-btn"
        data-action="save-name"
        aria-label=${e.saveName}
        title=${e.saveName}
        ?disabled=${!this.text.trim()||this.busy}
        @click=${()=>this.save()}
      >
        ${this.busy?ge("spinner","s spin"):ge("check","s")}
      </button>
      <button
        class="icon-btn"
        data-action="cancel-name"
        aria-label=${e.cancel}
        title=${e.cancel}
        ?disabled=${this.busy}
        @click=${()=>this.dispatchEvent(new CustomEvent("dm-cancel"))}
      >
        ${ge("close","s")}
      </button>
    </div>`}}Se.styles=ke,Se.properties={t:{attribute:!1},value:{},suffix:{},maxLength:{type:Number},busy:{type:Boolean},label:{},text:{state:!0}};class Ue extends de{constructor(){super(...arguments),this.accept="",this.sizeMb=25,this.files=[],this.overwrite=!1,this.busy=!1}async upload(){const e=[];let t;this.busy=!0;for(const i of this.files)try{e.push(await this.api.upload(this.target(i.name),i,this.overwrite))}catch(e){t=pe(e);break}this.busy=!1,this.files=[];const i=this.renderRoot.querySelector('input[type="file"]');i&&(i.value=""),this.dispatchEvent(new CustomEvent("dm-uploaded",{detail:{names:e,error:t}}))}render(){const e=this.t;return j`<div class="upload">
      <div class="line">
        <label class="check">
          <input
            type="checkbox"
            data-field="overwrite"
            .checked=${this.overwrite}
            ?disabled=${this.busy}
            @change=${e=>this.overwrite=e.target.checked}
          />
          ${e.replace}
        </label>
        <input
          type="file"
          multiple
          accept=${this.accept}
          aria-label=${e.chooseFiles}
          ?disabled=${this.busy}
          @change=${e=>this.files=[...e.target.files??[]]}
        />
        <button
          class="btn primary"
          data-action="upload"
          ?disabled=${!this.files.length||this.busy}
          @click=${()=>this.upload()}
        >
          ${this.busy?ge("spinner","s spin"):ge("upload","s")}
          ${e.upload}
        </button>
      </div>
      <p class="note">${$e(e.sizeNote,{n:this.sizeMb})}</p>
    </div>`}}Ue.styles=ke,Ue.properties={t:{attribute:!1},api:{attribute:!1},target:{attribute:!1},accept:{},sizeMb:{type:Number},files:{state:!0},overwrite:{state:!0},busy:{state:!0}},customElements.get("dm-rename-form")||customElements.define("dm-rename-form",Se),customElements.get("dm-upload-form")||customElements.define("dm-upload-form",Ue);class Ne extends de{constructor(){super(...arguments),this.locale="en",this.loading=!0,this.confirming=!1,this.renameBusy=!1,this.urls={}}willUpdate(){this.api&&this.api!==this.loaded&&(this.loaded=this.api,this.load())}async load(e=!1){e||(this.loading=!0),this.loadError=void 0;try{await this.fetch()}catch(e){const t=pe(e);he.has(t.code)?this.fatal(t):this.loadError=we(this.t,t)}finally{this.loading=!1}}toast(e){this.dispatchEvent(new CustomEvent("dm-toast",{detail:e,bubbles:!0,composed:!0}))}fatal(e){this.dispatchEvent(new CustomEvent("dm-fatal",{detail:e,bubbles:!0,composed:!0}))}fail(e){const t=pe(e);he.has(t.code)?this.fatal(t):this.toast($e(this.t.failed,{message:we(this.t,t)}))}inlineError(e){const t=pe(e);if(!he.has(t.code))return we(this.t,t);this.fatal(t)}render(){const e=this.t;return j`${this.loading?j`<div class="center" role="status" aria-label=${e.loading}>
            ${ge("spinner","spin")}
          </div>`:void 0!==this.loadError?j`<div class="alert" role="alert">
              ${ge("warning")}
              <span class="grow"
                >${$e(e.couldNotLoad,{message:this.loadError})}</span
              >
              <button
                class="btn"
                data-action="retry"
                @click=${()=>this.load()}
              >
                ${e.retry}
              </button>
            </div>`:this.renderContent()}
    ${this.renderConfirm()}`}ask(e){this.confirm=e}renderConfirm(){const e=this.confirm;if(!e)return K;const t=this.t,i=()=>{this.confirming||(this.confirm=void 0)};return j`<div class="scrim">
      <div
        class="dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        @keydown=${e=>"Escape"===e.key&&i()}
      >
        <h2 id="confirm-title">${e.title}</h2>
        ${e.lines.map(e=>j`<p>${e}</p>`)}
        <div class="dialog-actions">
          <button
            class="btn"
            data-action="cancel"
            ?disabled=${this.confirming}
            @click=${i}
          >
            ${t.cancel}
          </button>
          <button
            class="btn danger"
            data-action="confirm"
            ?disabled=${this.confirming}
            @click=${async()=>{this.confirming=!0;try{await e.run()}finally{this.confirming=!1,this.confirm=void 0}}}
          >
            ${this.confirming?ge("spinner","s spin"):K}${t.delete}
          </button>
        </div>
      </div>
    </div>`}async signAll(e){const t=await Promise.all(e.map(async e=>{try{return[this.api.mediaUrl(e),await this.api.signedUrl(e)]}catch{return[this.api.mediaUrl(e),""]}}));this.urls=Object.fromEntries(t)}previewUrl(e){return this.urls[this.api.mediaUrl(e)]||void 0}fileRow(e,t,i){const s=this.t,a=this.api.mediaUrl(e);if(this.renaming===a){const[i,a]=function(e){const t=e.lastIndexOf(".");return t>0?[e.slice(0,t),e.slice(t)]:[e,""]}(t.name);return j`<dm-rename-form
        class="file-row"
        .t=${s}
        .value=${i}
        .suffix=${a}
        .maxLength=${100}
        .busy=${this.renameBusy}
        @dm-save=${t=>this.renameFile(e,t.detail+a)}
        @dm-cancel=${()=>this.renaming=void 0}
      ></dm-rename-form>`}return j`<div class="file-row" data-file=${t.name}>
      <span class="fname" title=${t.name}>${t.name}</span>
      ${i?j`<span class="size"
              >${function(e,t){if(e>=xe)return`${new Intl.NumberFormat(t,{minimumFractionDigits:1,maximumFractionDigits:1}).format(e/xe)} MB`;return`${new Intl.NumberFormat(t).format(Math.ceil(e/1024))} KB`}(t.size,this.locale)}</span
            >`:K}
      <button
        class="icon-btn"
        data-action="rename-file"
        aria-label=${$e(s.rename,{name:t.name})}
        title=${$e(s.rename,{name:t.name})}
        @click=${()=>this.renaming=a}
      >
        ${ge("pencil","s")}
      </button>
      <button
        class="icon-btn danger"
        data-action="delete-file"
        aria-label=${$e(s.deleteName,{name:t.name})}
        title=${$e(s.deleteName,{name:t.name})}
        @click=${()=>this.ask({title:$e(s.deleteTitle,{name:t.name}),lines:[s.cannotUndo],run:()=>this.deleteFile(e,t.name)})}
      >
        ${ge("trash","s")}
      </button>
    </div>`}async renameFile(e,t){this.renameBusy=!0;try{const i=await this.api.call("PATCH",["media",...e],{name:t});this.renaming=void 0,i.name!==t&&this.toast($e(this.t.renamedTo,{name:i.name})),await this.load(!0)}catch(e){this.fail(e)}finally{this.renameBusy=!1}}async deleteFile(e,t){try{await this.api.call("DELETE",["media",...e]),this.toast($e(this.t.deletedName,{name:t})),await this.load(!0)}catch(e){this.fail(e)}}async uploaded(e){const{names:t,error:i}=e.detail;if(i){if(he.has(i.code))return void this.fail(i);{const e=we(this.t,i);this.toast(t.length?$e(this.t.failedAfter,{message:e,names:t.join(", ")}):$e(this.t.failed,{message:e}))}}else this.toast($e(this.t.uploaded,{names:t.join(", ")}));await this.load(!0)}}Ne.styles=ke,Ne.properties={api:{attribute:!1},t:{attribute:!1},locale:{attribute:!1},info:{attribute:!1},loading:{state:!0},loadError:{state:!0},confirm:{state:!0},confirming:{state:!0},renaming:{state:!0},renameBusy:{state:!0},urls:{state:!0}};const Te=["guest","resident","admin"],Me=["phone","watch","misc"],Ce=["ibeacon","mac","uuid"];class Pe extends Ne{constructor(){super(...arguments),this.users=[],this.haUsers=[],this.links={},this.saving=!1}async fetch(){const e=await this.api.users();this.users=e.users,this.haUsers=e.ha_users,this.links=e.links}haUserName(e){return e?this.haUsers.find(t=>t.id===e)?.name:void 0}renderContent(){const e=this.t;return j`<section class="card">
        <div class="card-head">
          <h2>${ge("users")}<span>${e.users}</span></h2>
          <button
            class="btn primary"
            data-action="add-user"
            @click=${()=>this.open(null)}
          >
            ${ge("userPlus","s")}${e.addUser}
          </button>
        </div>
        <ul class="rows">
          ${this.users.map(e=>this.renderUser(e))}
        </ul>
      </section>
      ${this.renderForm()}`}renderUser(e){const t=this.t,i=this.haUserName(this.links[e.id]),s=e.name===this.info.rootName;return j`<li
      class="row ${!1===e.isActive?"inactive":""}"
      data-user=${e.id}
      title=${!1===e.isActive?t.inactive:K}
    >
      <div class="who">
        <span class="name">${e.name}</span>
        ${i?j`<span class="sub" data-linked
                >${ge("link","s")}${$e(t.linkedTo,{name:i})}</span
              >`:K}
      </div>
      <span class="badge ${e.accessLevel}" data-badge
        >${t.access[e.accessLevel]??e.accessLevel}</span
      >
      <button
        class="icon-btn"
        data-action="edit"
        aria-label=${$e(t.editName,{name:e.name})}
        title=${$e(t.editName,{name:e.name})}
        @click=${()=>this.open(e)}
      >
        ${ge("pencil","s")}
      </button>
      ${s?j`<span class="icon-btn spacer" aria-hidden="true"></span>`:j`<button
              class="icon-btn danger"
              data-action="delete"
              aria-label=${$e(t.deleteName,{name:e.name})}
              title=${$e(t.deleteName,{name:e.name})}
              @click=${()=>this.ask({title:$e(t.deleteTitle,{name:e.name}),lines:[t.cannotUndo],run:()=>this.deleteUser(e)})}
            >
              ${ge("trash","s")}
            </button>`}
    </li>`}open(e){this.formError=void 0,this.draft=function(e,t){const i=Object.fromEntries(Me.map(t=>{const i=e?.bleData?.[t];return[t,{kind:i?.kind??"ibeacon",value:i?.value??""}]}));return e?{id:e.id,name:e.name,pin:e.pin,accessLevel:e.accessLevel,start:Ae(e.start),end:Ae(e.end),ble:i,haUser:t,storedStart:e.start}:{id:null,name:"",pin:"0000",accessLevel:"resident",start:Ee(),end:"",ble:i,haUser:"",storedStart:null}}(e,e?this.links[e.id]??"":"")}setDraft(e){this.draft&&(this.draft={...this.draft,...e})}pickHaUser(e){const t=this.draft,i=this.haUserName(t.haUser)??"",s=t.name.trim()&&t.name!==i?t.name:this.haUserName(e)??t.name;this.setDraft({haUser:e,name:s})}renderForm(){const e=this.draft;if(!e)return K;const t=this.t,i=new Set(Object.entries(this.links).filter(([t])=>t!==e.id).map(([,e])=>e));return j`<div class="scrim">
      <div
        class="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="user-title"
      >
        <h2 id="user-title">${e.id?t.editUser:t.addUser}</h2>
        ${this.formError?j`<div class="alert" role="alert">
                ${ge("warning")}<span class="grow">${this.formError}</span>
              </div>`:K}
        <form
          class="form"
          @submit=${e=>{e.preventDefault(),this.save()}}
        >
          <label class="field wide">
            ${t.haUser}
            <select
              data-field="haUser"
              ?disabled=${this.saving}
              @change=${e=>this.pickHaUser(e.target.value)}
            >
              <option value="" ?selected=${!e.haUser}>
                ${t.haUserNone}
              </option>
              ${this.haUsers.filter(e=>!i.has(e.id)).map(t=>j`<option
                      value=${t.id}
                      ?selected=${t.id===e.haUser}
                    >
                      ${t.name}
                    </option>`)}
            </select>
            <span class="hint">${t.haUserHint}</span>
          </label>
          <label class="field">
            ${t.name}
            <input
              type="text"
              data-field="name"
              .value=${e.name}
              ?disabled=${this.saving}
              @input=${e=>this.setDraft({name:e.target.value})}
            />
          </label>
          <label class="field">
            ${t.pin}
            <input
              type="text"
              data-field="pin"
              inputmode="numeric"
              autocomplete="off"
              maxlength="4"
              .value=${e.pin}
              ?disabled=${this.saving}
              @input=${e=>{const t=e.target;t.value=t.value.replace(/\D/g,"").slice(0,4),this.setDraft({pin:t.value})}}
            />
          </label>
          <label class="field">
            ${t.accessLevel}
            <select
              data-field="accessLevel"
              ?disabled=${this.saving}
              @change=${e=>this.setDraft({accessLevel:e.target.value})}
            >
              ${Te.map(i=>j`<option
                    value=${i}
                    ?selected=${i===e.accessLevel}
                  >
                    ${t.accessOption[i]}
                  </option>`)}
            </select>
          </label>
          <span></span>
          <label class="field">
            ${t.activeFrom}
            <input
              type="date"
              data-field="start"
              .value=${e.start}
              ?disabled=${this.saving}
              @change=${e=>this.setDraft({start:e.target.value})}
            />
          </label>
          <label class="field">
            ${t.activeUntil}
            <input
              type="date"
              data-field="end"
              .value=${e.end}
              ?disabled=${this.saving}
              @change=${e=>this.setDraft({end:e.target.value})}
            />
          </label>
          ${Me.map(e=>this.renderBle(e))}
          <button type="submit" hidden></button>
        </form>
        <div class="dialog-actions">
          <button
            class="btn"
            data-action="cancel"
            ?disabled=${this.saving}
            @click=${()=>this.draft=void 0}
          >
            ${t.cancel}
          </button>
          <button
            class="btn primary"
            data-action="save"
            ?disabled=${this.saving}
            @click=${()=>this.save()}
          >
            ${this.saving?ge("spinner","s spin"):K}${t.save}
          </button>
        </div>
      </div>
    </div>`}renderBle(e){const t=this.t,i=this.draft.ble[e],s=t=>this.setDraft({ble:{...this.draft.ble,[e]:{...i,...t}}});return j`<div class="field wide">
      <label class="field" for="ble-${e}">${t.ble[e]}</label>
      <div class="ble">
        <select
          data-field="ble-${e}-kind"
          aria-label=${$e(t.bleKindLabel,{slot:t.ble[e]})}
          ?disabled=${this.saving}
          @change=${e=>s({kind:e.target.value})}
        >
          ${Ce.map(e=>j`<option value=${e} ?selected=${e===i.kind}>
                ${t.bleKind[e]}
              </option>`)}
        </select>
        <input
          id="ble-${e}"
          type="text"
          data-field="ble-${e}"
          .value=${i.value}
          ?disabled=${this.saving}
          @input=${e=>s({value:e.target.value})}
        />
      </div>
    </div>`}record(e){const t=Object.fromEntries(Me.map(t=>{const i=e.ble[t].value.trim();return[t,i?{kind:e.ble[t].kind,value:i}:null]}));return{name:e.name,pin:e.pin,accessLevel:e.accessLevel,start:e.start?_e(e.start):e.storedStart??_e(Ee()),end:e.end?_e(e.end):null,bleData:t}}async save(){const e=this.draft;if(e&&!this.saving){this.saving=!0,this.formError=void 0;try{const t=await this.api.saveUser(e.id,this.record(e),e.haUser||null);this.draft=void 0,this.toast($e(this.t.savedName,{name:t.name})),await this.load(!0)}catch(e){const t=this.inlineError(e);void 0===t?this.draft=void 0:this.formError=t}finally{this.saving=!1}}}async deleteUser(e){try{await this.api.call("DELETE",["users",e.id]),this.toast($e(this.t.deletedName,{name:e.name})),await this.load(!0)}catch(e){this.fail(e)}}}Pe.properties={...Ne.properties,users:{state:!0},haUsers:{state:!0},links:{state:!0},draft:{state:!0},formError:{state:!0},saving:{state:!0}},customElements.get("dm-users-tab")||customElements.define("dm-users-tab",Pe);const De=e=>`${e.scope}/${e.mode}`;class Be extends Ne{constructor(){super(...arguments),this.savingKeys=new Set}async fetch(){this.data=await this.api.call("GET",["appearance"])}renderContent(){const e=this.data;return j`<p class="intro">${this.t.appearanceIntro}</p>
      <div class="modes">
        ${e.modes.map(({key:e,appearance:t})=>this.renderMode(e,t))}
      </div>`}renderMode(e,t){const i=this.t,s=this.data,a="house"===e.scope,n=this.savingKeys.has(De(e)),r=s.groups.find(e=>e.id===s.defaultGroup),o=a?r?$e(i.defaultGroup,{name:r.name}):i.defaultNone:i.sameAsHouse;return j`<section class="card mode" data-mode=${De(e)}>
      <div class="card-head">
        <h2>
          ${ge(a?"home":"party")}<span>${ye(i,e)}</span>
        </h2>
        ${n?j`<span class="tools" role="status" aria-label=${i.saving}
                >${ge("spinner","s spin")}</span
              >`:K}
      </div>
      <label class="field">
        ${i.theme}
        <select
          data-field="theme"
          .value=${t.theme??""}
          ?disabled=${n}
          @change=${i=>this.pick(e,{...t,theme:i.target.value||null})}
        >
          <option value="" ?selected=${null===t.theme}>
            ${a?i.themeDefault:i.sameAsHouse}
          </option>
          ${s.themes.map(e=>j`<option
                value=${e.id}
                ?selected=${e.id===t.theme}
              >
                ${e.label}
              </option>`)}
        </select>
      </label>
      <label class="field">
        ${i.bellMedia}
        <select
          data-field="mediaGroup"
          .value=${t.mediaGroup??""}
          ?disabled=${n}
          @change=${i=>this.pick(e,{...t,mediaGroup:i.target.value||null})}
        >
          <option value="" ?selected=${null===t.mediaGroup}>
            ${o}
          </option>
          ${s.groups.map(e=>j`<option
                value=${e.id}
                ?selected=${e.id===t.mediaGroup}
              >
                ${function(e,t){const i=1===t.files;return $e("video"===t.kind?i?e.groupVideo:e.groupVideos:i?e.groupSound:e.groupSounds,{name:t.name,n:t.files})}(i,e)}
              </option>`)}
        </select>
        <span class="hint" data-hint
          >${function(e,t,i,s){const a=t.groups.find(e=>e.id===s);return a?0===a.files?e.hintEmpty:"video"===a.kind?e.hintVideo:e.hintSound:"party"===i.scope?e.hintParty:t.defaultGroup?e.hintDefault:e.hintNone}(i,s,e,t.mediaGroup)}</span
        >
      </label>
    </section>`}setMode(e,t){this.data={...this.data,modes:this.data.modes.map(i=>De(i.key)===De(e)?{key:e,appearance:t}:i)}}async pick(e,t){const i=this.data.modes.find(t=>De(t.key)===De(e)).appearance;this.setMode(e,t),this.savingKeys=new Set(this.savingKeys).add(De(e));try{await this.api.call("PUT",["modes",e.scope,e.mode],t),this.toast(this.t.saved)}catch(t){this.setMode(e,i),this.fail(t)}finally{const t=new Set(this.savingKeys);t.delete(De(e)),this.savingKeys=t}}}Be.properties={...Ne.properties,data:{state:!0},savingKeys:{state:!0}},customElements.get("dm-appearance-tab")||customElements.define("dm-appearance-tab",Be);const Le={sound:".wav,.mp3,.ogg",video:".mp4,.webm,.mkv"},He={sound:25,video:200},Ge=(e,t)=>t.map(t=>ye(e,t)).join(", ");function Ie(e,t){const i=t.files.length,s=[0===i?e.deleteGroupEmpty:1===i?e.deleteGroupOne:$e(e.deleteGroupMany,{n:i})];return t.usedBy.length&&s.push($e(e.modesFallBack,{modes:Ge(e,t.usedBy)})),s.push(e.cannotUndo),s}class Oe extends Ne{constructor(){super(...arguments),this.groups=[],this.newName="",this.newKind="sound",this.creating=!1,this.groupBusy=!1}async fetch(){const e=await this.api.call("GET",["media"]);this.groups=e.groups,await this.signAll(e.groups.flatMap(e=>e.files.map(t=>this.path(e,t.name))))}path(e,t){return["groups",e.id,t]}renderContent(){const e=this.t;return j`${this.renderNewGroup()}
    ${this.groups.length?this.groups.map(e=>this.renderGroup(e)):j`<section class="card">
            <p class="muted" data-empty>${e.noGroups}</p>
          </section>`}`}renderNewGroup(){const e=this.t;return j`<section class="card">
      <div class="card-head">
        <h2>${ge("folderPlus")}<span>${e.newGroup}</span></h2>
      </div>
      <p class="intro">${e.newGroupIntro}</p>
      <form
        class="inline-form"
        @submit=${e=>{e.preventDefault(),this.create()}}
      >
        <input
          type="text"
          data-field="group-name"
          maxlength="64"
          aria-label=${e.groupName}
          placeholder=${e.groupNamePlaceholder}
          .value=${this.newName}
          ?disabled=${this.creating}
          @input=${e=>this.newName=e.target.value}
        />
        <select
          data-field="group-kind"
          aria-label=${e.kind}
          ?disabled=${this.creating}
          @change=${e=>this.newKind=e.target.value}
        >
          <option value="sound" ?selected=${"sound"===this.newKind}>
            ${e.kindSounds}
          </option>
          <option value="video" ?selected=${"video"===this.newKind}>
            ${e.kindVideos}
          </option>
        </select>
        <button
          class="btn primary"
          type="submit"
          data-action="create"
          ?disabled=${!this.newName.trim()||this.creating}
        >
          ${this.creating?ge("spinner","s spin"):ge("plus","s")}
          ${e.create}
        </button>
      </form>
    </section>`}renderGroup(e){const t=this.t,i="video"===e.kind;return j`<section class="card" data-group=${e.id}>
      <div class="card-head">
        ${this.renamingGroup===e.id?j`${ge(i?"film":"music")}
                <dm-rename-form
                  style="flex:1"
                  .t=${t}
                  .value=${e.name}
                  .maxLength=${64}
                  .label=${t.groupName}
                  .busy=${this.groupBusy}
                  @dm-save=${t=>this.renameGroup(e,t.detail)}
                  @dm-cancel=${()=>this.renamingGroup=void 0}
                ></dm-rename-form>`:j`<h2>
                  ${ge(i?"film":"music")}<span>${e.name}</span>
                </h2>
                <div class="tools">
                  ${e.isDefault?j`<span class="badge default" data-badge="default"
                          >${t.defaultBadge}</span
                        >`:K}
                  <span class="badge" data-badge="kind"
                    >${i?t.kindVideos:t.kindSounds}</span
                  >
                  <button
                    class="icon-btn"
                    data-action="rename-group"
                    aria-label=${t.renameGroup}
                    title=${t.renameGroup}
                    @click=${()=>this.renamingGroup=e.id}
                  >
                    ${ge("pencil","s")}
                  </button>
                  <button
                    class="icon-btn danger"
                    data-action="delete-group"
                    aria-label=${t.deleteGroup}
                    title=${t.deleteGroup}
                    @click=${()=>this.ask({title:$e(t.deleteTitle,{name:e.name}),lines:Ie(t,e),run:()=>this.deleteGroup(e)})}
                  >
                    ${ge("trash","s")}
                  </button>
                </div>`}
      </div>
      <p class="intro" data-usage>${function(e,t){const i=Ge(e,t.usedBy);return t.usedBy.length&&t.isDefault?$e(e.usedAndDefault,{modes:i}):t.usedBy.length?$e(e.used,{modes:i}):t.isDefault?e.defaultOnly:e.unused}(t,e)}</p>
      ${e.files.length?i?j`<div class="grid videos">
                ${e.files.map(t=>{const i=this.path(e,t.name),s=this.previewUrl(i);return j`<div>
                    ${s?j`<video
                            controls
                            preload="metadata"
                            src=${s}
                          ></video>`:K}
                    ${this.fileRow(i,t,!0)}
                  </div>`})}
              </div>`:j`<div>
                ${e.files.map(t=>{const i=this.path(e,t.name),s=this.previewUrl(i);return j`<div class="sound">
                    ${this.fileRow(i,t,!0)}
                    ${s?j`<audio
                            controls
                            preload="none"
                            src=${s}
                          ></audio>`:K}
                  </div>`})}
              </div>`:j`<p class="muted" data-empty>
              ${i?t.noVideos:t.noSounds}
            </p>`}
      <dm-upload-form
        .t=${t}
        .api=${this.api}
        .target=${t=>this.path(e,t)}
        accept=${Le[e.kind]}
        .sizeMb=${He[e.kind]}
        @dm-uploaded=${e=>this.uploaded(e)}
      ></dm-upload-form>
    </section>`}async create(){const e=this.newName.trim();if(e&&!this.creating){this.creating=!0;try{const t=await this.api.call("POST",["media-groups"],{name:e,kind:this.newKind});this.newName="",this.toast($e(this.t.createdName,{name:t.name})),await this.load(!0)}catch(e){this.fail(e)}finally{this.creating=!1}}}async renameGroup(e,t){this.groupBusy=!0;try{await this.api.call("PATCH",["media-groups",e.id],{name:t}),this.renamingGroup=void 0,await this.load(!0)}catch(e){this.fail(e)}finally{this.groupBusy=!1}}async deleteGroup(e){try{await this.api.call("DELETE",["media-groups",e.id]),this.toast($e(this.t.deletedName,{name:e.name})),await this.load(!0)}catch(e){this.fail(e)}}}Oe.properties={...Ne.properties,groups:{state:!0},newName:{state:!0},newKind:{state:!0},creating:{state:!0},renamingGroup:{state:!0},groupBusy:{state:!0}},customElements.get("dm-media-tab")||customElements.define("dm-media-tab",Oe);const Re=e=>["photos",e];class ze extends Ne{constructor(){super(...arguments),this.photos=[]}async fetch(){const e=await this.api.call("GET",["media"]);this.photos=e.photos,await this.signAll(e.photos.map(e=>Re(e.name)))}renderContent(){const e=this.t;return j`<section class="card">
      <div class="card-head">
        <h2>${ge("image")}<span>${e.photosTitle}</span></h2>
      </div>
      <p class="intro">${e.photosIntro}</p>
      ${this.photos.length?j`<div class="grid photos">
              ${this.photos.map(e=>{const t=this.previewUrl(Re(e.name));return j`<div class="photo">
                  ${t?j`<img
                          src=${t}
                          alt=${e.name}
                          loading="lazy"
                        />`:K}
                  ${this.fileRow(Re(e.name),e,!1)}
                </div>`})}
            </div>`:j`<p class="muted" data-empty>${e.noPhotos}</p>`}
      <dm-upload-form
        .t=${e}
        .api=${this.api}
        .target=${Re}
        accept=".gif,.jpeg,.jpg,.png,.webp"
        .sizeMb=${25}
        @dm-uploaded=${e=>this.uploaded(e)}
      ></dm-upload-form>
    </section>`}}ze.properties={...Ne.properties,photos:{state:!0}},customElements.get("dm-photos-tab")||customElements.define("dm-photos-tab",ze);const je=["users","appearance","media-groups","photos"];class Ve extends de{constructor(){super(...arguments),this.narrow=!1,this.loading=!0,this.started=!1}get t(){return be(this.hass)}get tabs(){const e=this.info?.info?.features??[];return je.filter(t=>e.includes(t))}willUpdate(e){e.has("hass")&&this.hass&&(this.api&&(this.api.hass=this.hass),this.started||(this.started=!0,this.loadInfo()))}async loadInfo(e){this.loading=!0,this.loadError=void 0,this.page=void 0;try{const t=await this.hass.callWS({type:"doormonitor/admin/info",...e?{entry_id:e}:{}});this.info=t,t.entry_id?t.configured?t.error?this.onError(new ce(t.error.message,t.error.code)):(this.api?.entryId!==t.entry_id&&(this.api=new ue(this.hass,t.entry_id)),this.tab&&this.tabs.includes(this.tab)||(this.tab=this.tabs[0])):this.page={kind:"not-configured"}:this.page={kind:"no-entries"}}catch(e){this.loadError=we(this.t,pe(e))}finally{this.loading=!1}}onError(e){"not-admin"===e.code?this.page={kind:"not-admin"}:"bad-token"===e.code?this.page={kind:"bad-token"}:"not-configured"===e.code?this.page={kind:"not-configured"}:this.loadError=we(this.t,e)}showToast(e){this.toastText=e,window.clearTimeout(this.toastTimer),this.toastTimer=window.setTimeout(()=>this.toastText=void 0,2200)}openSettings(){history.pushState(null,"","/config/integrations/integration/doormonitor"),window.dispatchEvent(new CustomEvent("location-changed",{detail:{replace:!1}}))}toggleMenu(){this.dispatchEvent(new Event("hass-toggle-menu",{bubbles:!0,composed:!0}))}disconnectedCallback(){super.disconnectedCallback(),window.clearTimeout(this.toastTimer)}render(){const e=this.t;return j`${this.renderBar()}
      <main
        @dm-toast=${e=>this.showToast(e.detail)}
        @dm-fatal=${e=>this.onError(e.detail)}
      >
        ${this.loading?j`<div class="center" role="status" aria-label=${e.loading}>
                ${ge("spinner","spin")}
              </div>`:this.page?this.renderPage(this.page):void 0!==this.loadError?j`<div class="alert" role="alert">
                    ${ge("warning")}
                    <span class="grow"
                      >${$e(e.couldNotLoad,{message:this.loadError})}</span
                    >
                    <button
                      class="btn"
                      data-action="retry"
                      @click=${()=>this.loadInfo(this.info?.entry_id)}
                    >
                      ${e.retry}
                    </button>
                  </div>`:this.renderTab()}
      </main>
      ${this.toastText?j`<div class="toast" role="status" aria-live="polite">
              ${this.toastText}
            </div>`:K}`}renderBar(){const e=this.t,t=this.info?.entries??[],i=!this.loading&&!this.page&&void 0===this.loadError;return j`<header class="bar">
      <div class="bar-top">
        ${this.narrow?j`<button
                class="icon-btn"
                aria-label=${e.menu}
                @click=${this.toggleMenu}
              >
                ${ge("menu")}
              </button>`:K}
        <h1>${ge("bell")}<span>${e.title}</span></h1>
        ${t.length>1?j`<select
                aria-label=${e.entry}
                data-field="entry"
                .value=${this.info?.entry_id??""}
                @change=${e=>this.loadInfo(e.target.value)}
              >
                ${t.map(e=>j`<option
                      value=${e.entry_id}
                      ?selected=${e.entry_id===this.info?.entry_id}
                    >
                      ${e.title}
                    </option>`)}
              </select>`:K}
        ${this.info?.actor_name&&i?j`<span class="acting"
                >${$e(e.actingAs,{name:this.info.actor_name})}</span
              >`:K}
        <button
          class="icon-btn cog"
          data-action="settings"
          aria-label=${e.settings}
          title=${e.settings}
          @click=${this.openSettings}
        >
          ${ge("cog")}
        </button>
      </div>
      ${i&&this.tabs.length?j`<nav role="tablist">
              ${this.tabs.map(t=>j`<button
                    role="tab"
                    data-tab=${t}
                    aria-selected=${t===this.tab?"true":"false"}
                    @click=${()=>this.tab=t}
                  >
                    ${e.tabs[t]}
                  </button>`)}
            </nav>`:K}
    </header>`}renderPage(e){const t=this.t,[i,s]={"no-entries":[t.notSetUpTitle,t.notSetUpBody],"not-configured":[t.notConfiguredTitle,t.notConfiguredBody],"not-admin":[t.notAdminTitle,$e(t.notAdminBody,{name:this.info?.actor_name||"–"})],"bad-token":[t.badTokenTitle,t.badTokenBody]}[e.kind];return j`<section class="card page" data-page=${e.kind}>
      <h2>${i}</h2>
      <p>${s}</p>
      ${"no-entries"===e.kind?K:j`<button class="btn primary" @click=${this.openSettings}>
              ${ge("cog","s")}${t.openSettings}
            </button>`}
    </section>`}renderTab(){const e=this.t;if(!this.tabs.length)return j`<p class="muted" data-page="no-features">${e.noFeatures}</p>`;const t=this.api,i=e,s=function(e){const t=String(e?.language||e?.locale?.language||"en").toLowerCase().replace(/_/g,"-").replace(/^(no|nn)(-|$)/,"nb$2");try{return Intl.getCanonicalLocales(t)[0]||"en"}catch{return"en"}}(this.hass),a=this.info.info;switch(this.tab){case"users":return j`<dm-users-tab
          .api=${t}
          .t=${i}
          .locale=${s}
          .info=${a}
        ></dm-users-tab>`;case"appearance":return j`<dm-appearance-tab
          .api=${t}
          .t=${i}
          .locale=${s}
          .info=${a}
        ></dm-appearance-tab>`;case"media-groups":return j`<dm-media-tab
          .api=${t}
          .t=${i}
          .locale=${s}
          .info=${a}
        ></dm-media-tab>`;case"photos":return j`<dm-photos-tab
          .api=${t}
          .t=${i}
          .locale=${s}
          .info=${a}
        ></dm-photos-tab>`;default:return K}}}Ve.styles=[ke,n`
      :host {
        min-height: 100%;
        background: var(--primary-background-color);
      }
      .bar {
        position: sticky;
        top: 0;
        z-index: 2;
        background: var(
          --app-header-background-color,
          var(--primary-background-color)
        );
        color: var(--app-header-text-color, var(--primary-text-color));
        border-bottom: 1px solid var(--dm-line);
      }
      .bar-top {
        display: flex;
        align-items: center;
        gap: 10px;
        min-height: 56px;
        padding: 0 12px 0 16px;
        max-width: 1048px;
        margin: 0 auto;
      }
      .bar-top h1 {
        font-size: 1.25rem;
        font-weight: 500;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
        flex: 1;
        min-width: 0;
      }
      .bar .icon-btn {
        color: inherit;
      }
      .acting {
        color: var(--dm-muted);
        font-size: 0.9rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      :host([narrow]) .acting {
        display: none;
      }
      .bar select {
        width: auto;
        max-width: 40vw;
      }
      .cog {
        width: 44px;
        height: 44px;
      }
      nav {
        display: flex;
        gap: 4px;
        overflow-x: auto;
        max-width: 1048px;
        margin: 0 auto;
        padding: 0 12px;
      }
      nav button {
        font: inherit;
        color: var(--dm-muted);
        background: none;
        border: none;
        border-bottom: 2px solid transparent;
        padding: 10px 12px;
        cursor: pointer;
        white-space: nowrap;
      }
      nav button[aria-selected="true"] {
        color: var(--dm-text);
        border-bottom-color: var(--dm-accent);
      }
      main {
        max-width: 1048px;
        margin: 0 auto;
        padding: 16px 24px 96px;
      }
      :host([narrow]) main {
        padding: 12px 12px 96px;
      }
      .page {
        max-width: 560px;
        margin: 32px auto;
      }
      .page h2 {
        margin: 0 0 8px;
        font-size: 1.2rem;
      }
      .page p {
        line-height: 1.5;
        color: var(--dm-muted);
      }
      .toast {
        position: fixed;
        left: 50%;
        bottom: 24px;
        transform: translateX(-50%);
        z-index: 20;
        background: var(--dm-text);
        color: var(--primary-background-color, #fff);
        padding: 10px 18px;
        border-radius: 999px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
        max-width: calc(100vw - 32px);
      }
    `],Ve.properties={hass:{attribute:!1},narrow:{type:Boolean,reflect:!0},route:{attribute:!1},panel:{attribute:!1},info:{state:!0},loading:{state:!0},loadError:{state:!0},page:{state:!0},tab:{state:!0},toastText:{state:!0},api:{state:!0}},customElements.get("doormonitor-admin-panel")||customElements.define("doormonitor-admin-panel",Ve);export{Ve as DoorMonitorAdminPanel,je as TABS};
