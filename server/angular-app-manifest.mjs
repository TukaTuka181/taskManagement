
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
    'index.csr.html': {size: 25034, hash: 'f433be3738be970154aaad607736838d150955db704ea539191a9e56de06fa77', text: () => import('./assets-chunks/index_csr_html.mjs').then(m => m.default)},
    'index.server.html': {size: 17487, hash: '2578a98bd80e2177c830692e0738cdeafb859cb04f7fa1f42adcb609a3c81ae3', text: () => import('./assets-chunks/index_server_html.mjs').then(m => m.default)},
    'index.html': {size: 62653, hash: '0adfadb342679c9042eaf6cf9829420b6b791237cbbd6d4fb73b8e5bb6288ed2', text: () => import('./assets-chunks/index_html.mjs').then(m => m.default)},
    'styles-DTTV3AOM.css': {size: 8100, hash: 'jHWbwFO0LXY', text: () => import('./assets-chunks/styles-DTTV3AOM_css.mjs').then(m => m.default)}
  },
};
