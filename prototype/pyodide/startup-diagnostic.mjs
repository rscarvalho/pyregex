// Isolated experiment: instrument served copies, never change the controller/runtime pins.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import os from 'node:os';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';
import { chromium } from 'playwright';
import { distribution, runtimeTransfer } from './performance-stats.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const config = JSON.parse(await readFile(resolve(here, 'runtime.json')));
const names = ['pyodide.mjs', 'pyodide.asm.mjs', 'pyodide.asm.wasm',
  'python_stdlib.zip', 'pyodide-lock.json'];
const assetDirectory = '/tmp/opencode/pyodide-startup-assets-314.0.7';
await mkdir(assetDirectory, { recursive: true });
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const assets = new Map();
const manifest = [];
for (const name of names) {
  const response = await fetch(config.indexURL + name);
  assert.equal(response.ok, true, `Download ${name}`);
  const bytes = Buffer.from(await response.arrayBuffer());
  await writeFile(resolve(assetDirectory, name), bytes);
  const compressed = gzipSync(bytes);
  assets.set(`/runtime/${name}`, { compressed, type: name.endsWith('.wasm') ?
    'application/wasm' : name.endsWith('.mjs') ? 'text/javascript' :
      name.endsWith('.json') ? 'application/json' : 'application/zip' });
  manifest.push({ name, url: response.url, decodedBytes: bytes.length,
    sha256: sha(bytes), localGzipBytes: compressed.length });
}
const sourceNames = ['startup-diagnostic.mjs', 'performance.html', 'performance-page.mjs',
  'controller.mjs', 'limits.mjs', 'worker.mjs', 'runtime.json', 'evaluator.py', 'performance-stats.mjs'];
const sources = new Map(await Promise.all(sourceNames.map(async name =>
  [name, await readFile(resolve(here, name), 'utf8')])));
const replaceOnce = (source, needle, replacement) => {
  assert.equal(source.split(needle).length, 2, `Instrumentation anchor: ${needle}`);
  return source.replace(needle, replacement);
};
let worker = sources.get('worker.mjs');
for (const [needle, replacement] of [
  ['let runtime;', "globalThis.startupMarks = { workerModuleEntered: performance.now() };\nconst mark = name => { startupMarks[name] = performance.now(); };\nlet runtime;"],
  ["  const response = await fetch('./runtime.json');", "  mark('initializeEntered');\n  const response = await fetch('./runtime.json');"],
  ['  const { loadPyodide } =', "  mark('pinFetched');\n  const { loadPyodide } ="],
  ['  runtime = await loadPyodide({ indexURL: config.indexURL });',
    "  mark('loaderImported');\n  runtime = await loadPyodide({ indexURL: config.indexURL, fsInit() { mark('fsInitBeforeInterpreter'); } });\n  mark('loadPyodideResolved');"],
  ['  runtime.runPython(await source.text());', "  const text = await source.text();\n  mark('evaluatorFetched');\n  runtime.runPython(text);\n  mark('evaluatorInstalled');"],
  ['  return { pyodide: runtime.version, python };', "  mark('versionsChecked');\n  return { pyodide: runtime.version, python };"]
]) worker = replaceOnce(worker, needle, replacement);
const pageSource = replaceOnce(sources.get('performance-page.mjs'),
  'window.performanceController = new RegexController();',
  `window.startupMarks = {};
window.performanceController = new RegexController({ createWorker() {
  startupMarks.workerConstructionStart = performance.now();
  const worker = new Worker('./worker.mjs', { type: 'module' });
  startupMarks.workerConstructionReturned = performance.now();
  return worker;
} });`);
const allowed = new Map([...sources].filter(([name]) => name !== 'startup-diagnostic.mjs'));
allowed.set('worker.mjs', worker);
allowed.set('performance-page.mjs', pageSource);
let condition;
const server = createServer((req, res) => {
  const asset = assets.get(req.url);
  if (asset) {
    res.writeHead(200, { 'Content-Type': asset.type, 'Content-Encoding': 'gzip',
      'Cache-Control': 'public, max-age=3600' });
    res.end(asset.compressed);
    return;
  }
  const name = req.url === '/' ? 'performance.html' : req.url.slice(1);
  if (!allowed.has(name)) { res.writeHead(404).end(); return; }
  const body = name === 'runtime.json' && condition === 'loopback' ?
    JSON.stringify({ ...config, indexURL: `http://127.0.0.1:${server.address().port}/runtime/` }) :
    allowed.get(name);
  res.writeHead(200, { 'Content-Type': name.endsWith('.mjs') ? 'text/javascript' :
    name.endsWith('.html') ? 'text/html' : name.endsWith('.json') ? 'application/json' : 'text/plain',
  'Cache-Control': 'no-store' });
  res.end(body);
});
const cpu = () => ({ at: new Date().toISOString(), loadAverage: os.loadavg(),
  cpus: os.cpus().map(({ times }) => times) });
const pairs = [];
const errors = [];
let browser;
let browserVersion;
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
try {
  for (let repeat = 0; repeat < 3; repeat++) {
    // Alternate order to reduce (not eliminate) time/order bias.
    for (condition of repeat % 2 ? ['loopback', 'cdn'] : ['cdn', 'loopback']) {
      browser = await chromium.launch();
      browserVersion = browser.version();
      const context = await browser.newContext({ serviceWorkers: 'block' });
      const pair = { condition, repeat: repeat + 1 };
      for (const phase of ['cold', 'warm']) {
        const before = cpu();
        const page = await context.newPage();
        page.on('pageerror', error => errors.push(String(error)));
        await page.goto(`http://127.0.0.1:${server.address().port}/`);
        await page.waitForFunction(() => window.performanceReady !== undefined);
        const ready = await page.evaluate(() => window.performanceReady);
        assert.equal(ready.versions.pyodide, config.pyodide);
        assert.equal(ready.versions.python, config.python);
        assert.equal(page.workers().length, 1);
        const workerData = await page.workers()[0].evaluate(() => ({
          timeOrigin: performance.timeOrigin, marks: startupMarks,
          resources: performance.getEntriesByType('resource').map(row => row.toJSON())
        }));
        const pageData = await page.evaluate(async () => {
          const subsequentProbeMs = [];
          for (let i = 0; i < 10; i++) {
            const start = performance.now();
            const result = await performanceController.evaluate([
              { id: 'ready', operation: 'search', flags: [], pattern: 'a+', input: 'baaa' }
            ]);
            if (result.results[0].result.group !== 'aaa') throw new Error('Probe failed');
            subsequentProbeMs.push(performance.now() - start);
          }
          return { timeOrigin: performance.timeOrigin, marks: startupMarks,
            resources: performance.getEntriesByType('resource').map(row => row.toJSON()),
            navigation: performance.getEntriesByType('navigation').map(row => row.toJSON()),
            subsequentProbeMs };
        });
        const indexURL = condition === 'cdn' ? config.indexURL :
          `http://127.0.0.1:${server.address().port}/runtime/`;
        const transfer = runtimeTransfer(workerData.resources, indexURL);
        assert.equal(transfer.measurable, true);
        assert.equal(transfer.allLocalCache, phase === 'warm');
        if (phase === 'cold') assert.equal(transfer.resources.every(row => row.transferSize > 0), true);
        pair[phase] = { ...ready, before, after: cpu(), page: pageData,
          worker: workerData, transfer };
        await page.close();
      }
      pairs.push(pair);
      await context.close();
      await browser.close();
      browser = null;
    }
  }
  assert.deepEqual(errors, []);
  const summary = Object.fromEntries(['cdn', 'loopback'].map(name => [name,
    Object.fromEntries(['cold', 'warm'].map(phase => [phase,
      distribution(pairs.filter(row => row.condition === name).map(row => row[phase].navigationToUsableMs))]))]));
  console.log(JSON.stringify({ scope: 'issue42-startup-diagnostic-not-runtime-go',
    measuredAt: new Date().toISOString(), baseCommit: execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(),
    sourceSha256: Object.fromEntries([...sources].map(([name, text]) => [name, sha(text)])),
    servedInstrumentationSha256: { worker: sha(worker), page: sha(pageSource) },
    config, assets: manifest, assetDirectory, versions: { chromium: browserVersion, node: process.version, playwright: '1.65.0' },
    device: { cpu: os.cpus()[0].model, logicalCpus: os.cpus().length, release: os.release(), totalMemory: os.totalmem() },
    definitions: { samples: '3 independent browser/context cold-warm pairs per condition; 12 startups; no discarded samples; alternating condition order',
      cold: 'Fresh browser/context; every runtime resource reports positive transferSize; OS/DNS/CDN and machine code caches not controlled',
      warm: 'New page and worker in primed context; all five runtime resource transferSize zero and body sizes positive',
      readiness: 'Unchanged navigation-to-first-successful-probe boundary, 30s startup safety and 2s evaluation deadline',
      fsInit: 'Documented hook before main/interpreter start, empty site-packages guaranteed; not an exact WASM completion or Python initialization duration',
      resources: 'Worker and page time origins recorded separately; Resource Timing fetch spans overlap initialization/streaming compilation, not additive CPU phases',
      loopback: 'Identical decoded pinned assets freshly downloaded and SHA256 recorded, local gzip, experimental indexURL only; not a production hosting switch or CDN compression comparison',
      cpu: 'Per-logical-CPU cumulative times and load averages before/after each startup; shared-host load, power, uplink uncontrolled' },
    unobservable: ['Separate WASM compilation and instantiation', 'Exact Python interpreter initialization versus Pyodide bootstrap', 'Browser code-cache hits', 'Peak/total memory; mobile hardware'],
    summary, pairs, pageErrors: errors }, null, 2));
} finally {
  await browser?.close();
  await new Promise(resolve => server.close(resolve));
}
