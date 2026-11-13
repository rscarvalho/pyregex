// Partial fallback only: a page isolate's heap is NOT the app's worker/total memory.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const here = dirname(fileURLToPath(import.meta.url));
const files = ['performance.html', 'performance-page.mjs', 'controller.mjs',
  'limits.mjs', 'worker.mjs', 'runtime.json', 'evaluator.py'];
const sourceSha256 = Object.fromEntries(await Promise.all([...files, 'memory-cdp.mjs'].map(async name =>
  [name, createHash('sha256').update(await readFile(resolve(here, name))).digest('hex')])));
const allowed = new Map(files.map(name => [`/${name}`, name]));
allowed.set('/', 'performance.html');
const server = createServer(async (req, res) => {
  const name = allowed.get(req.url);
  if (!name) { res.writeHead(404).end(); return; }
  try {
    res.writeHead(200, { 'Content-Type': name.endsWith('.mjs') ? 'text/javascript' :
      name.endsWith('.html') ? 'text/html' : name.endsWith('.json') ? 'application/json' : 'text/plain',
    'Cache-Control': 'no-store', 'Cross-Origin-Opener-Policy': 'same-origin',
    'Cross-Origin-Embedder-Policy': 'require-corp' });
    res.end(await readFile(resolve(here, name)));
  } catch { res.destroy(); }
});
const watchdog = setTimeout(() => { console.error('CDP memory 45 s watchdog'); process.exit(2); }, 45000);
let browser;
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
try {
  browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  await page.goto(`http://127.0.0.1:${server.address().port}/`);
  await page.waitForFunction(() => window.performanceReady !== undefined);
  const ready = await page.evaluate(() => window.performanceReady);
  assert.equal(page.workers().length, 1);
  const session = await page.context().newCDPSession(page);
  let sample;
  try { sample = { status: 'measured-partial', value: await session.send('Runtime.getHeapUsage', {}, { timeout: 3000 }) }; }
  catch (error) { sample = { status: 'failed', error: String(error) }; }
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({ scope: 'issue42-page-isolate-only-not-total-memory',
    measuredAt: new Date().toISOString(), sourceSha256,
    chromium: browser.version(), node: process.version, playwright: '1.65.0', ready,
    method: 'CDP Runtime.getHeapUsage', sample, targetBytes: 256 * 1024 * 1024,
    gateStatus: 'inconclusive',
    limitations: ['One isolate-level page JS heap sample; live Pyodide worker is NOT included',
      'usedSize and totalSize are JS heap usage/allocation, not total memory or RSS',
      'embedderHeapUsedSize and backingStorageSize are separate protocol fields; no invented sum or peak bound',
      'Separate isolated diagnostic, unchanged controller/worker; not production security validation'] }, null, 2));
} finally {
  clearTimeout(watchdog);
  await browser?.close();
  await new Promise(resolve => server.close(resolve));
}
