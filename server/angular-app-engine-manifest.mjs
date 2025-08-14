
export default {
  basePath: 'https://TukaTuka181.github.io/taskManagement',
  supportedLocales: {
  "en-US": ""
},
  entryPoints: {
    '': () => import('./main.server.mjs')
  },
};
