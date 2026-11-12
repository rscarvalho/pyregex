// Historical sources stay unchanged; only disposable local output differs.
const fs = require('fs');
const grunt = require('grunt');
grunt.tasks(['build'], {}, () => {
  const bundle = 'public/assets/application.js';
  const js = fs.readFileSync(bundle, 'utf8');
  if (!js.includes('http://localhost:5000/api')) throw new Error('Missing API configuration');
  fs.writeFileSync(bundle, js.replace('http://localhost:5000/api', 'http://127.0.0.1:5000/api'));
  let html = fs.readFileSync('public/index.html', 'utf8');
  html = html.replace(/<script>\s*\(function\(i,s,o,g,r,a,m\)[\s\S]*?<\/script>/, '');
  html = html.replace(/<link\b[^>]*href=['"](?:https?:)?\/\/[^>]*>/g, '');
  html = html.replace(/<img\b[^>]*src=['"]https?:\/\/[^>]*>/g, '');
  fs.writeFileSync('public/index.html', html);
});
