const http = require('http');
const fs = require('fs');
const path = require('path');
const root = '/app/public';
const types = {'.html':'text/html', '.js':'application/javascript', '.css':'text/css', '.png':'image/png', '.gif':'image/gif', '.ico':'image/x-icon'};
http.createServer((request, response) => {
  let pathname;
  try { pathname = decodeURIComponent(new URL(request.url, 'http://local').pathname); }
  catch (_) { response.writeHead(400).end(); return; }
  const filename = path.resolve(root, '.' + pathname);
  if (!filename.startsWith(root + '/') && filename !== root) {
    response.writeHead(403).end(); return;
  }
  const file = pathname === '/' || pathname === '/changelog' ? root + '/index.html' : filename;
  fs.readFile(file, (error, bytes) => {
    response.setHeader('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' http://127.0.0.1:5000; object-src 'none'; base-uri 'self'");
    if (error) { response.writeHead(404).end(); return; }
    response.setHeader('Content-Type', types[path.extname(file)] || 'application/octet-stream');
    response.end(bytes);
  });
}).listen(8082, '0.0.0.0');
