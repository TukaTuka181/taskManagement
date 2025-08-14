
export default {
  bootstrap: () => import('./main.server.mjs').then(m => m.default),
  inlineCriticalCss: true,
  baseHref: 'https://TukaTuka181.github.io/taskManagement',
  locale: undefined,
  routes: [
  {
    "renderMode": 2,
    "route": "/taskManagement"
  }
],
  entryPointToBrowserMapping: undefined,
  assets: {
    'index.csr.html': {size: 482, hash: '314d4a4daeef49f5ce663fe03cb762560d3839b27dcccba78ba2b0a29b90c530', text: () => import('./assets-chunks/index_csr_html.mjs').then(m => m.default)},
    'index.server.html': {size: 995, hash: 'e61080315c6ec91425dbb12fc2cb25da69592ae6a01d2681ec82d501fad5c0dd', text: () => import('./assets-chunks/index_server_html.mjs').then(m => m.default)},
    'index.html': {size: 21620, hash: '4e23367f9817108bc9f2a98502f0700aa15323bdd706f32143abf6bcffcf40fe', text: () => import('./assets-chunks/index_html.mjs').then(m => m.default)},
    'styles-5INURTSO.css': {size: 0, hash: 'menYUTfbRu8', text: () => import('./assets-chunks/styles-5INURTSO_css.mjs').then(m => m.default)}
  },
};
