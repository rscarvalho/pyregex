import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import os from 'node:os';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { distribution, runtimeTransfer } from './performance-stats.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const config = JSON.parse(await readFile(resolve(here, 'runtime.json')));
const files = new Map([
  ['/', ['performance.html', 'text/html']],
  ...['performance-page.mjs', 'controller.mjs', 'limits.mjs', 'worker.mjs'].map(name =>
    [`/${name}`, [name, 'text/javascript']]),
  ['/runtime.json', ['runtime.json', 'application/json']],
  ['/evaluator.py', ['evaluator.py', 'text/plain']]
]);
const server = createServer(async (req, res) => {
  const entry = files.get(req.url);
  if (!entry) { res.writeHead(404).end(); return; }
  try {
    res.writeHead(200, { 'Content-Type': entry[1], 'Cache-Control': 'no-store' });
    res.end(await readFile(resolve(here, entry[0])));
  } catch { res.destroy(); }
});
const workloads = [
  { id: 'log-search', operation: 'search', flags: ['MULTILINE'],
    pattern: '^ERROR: (.+)$', input: 'INFO: ordinary line\n'.repeat(200) + 'ERROR: failed' },
  { id: 'unicode-match', operation: 'match', flags: [],
    pattern: '^(é😀é)+$', input: 'é😀é'.repeat(200) },
  { id: 'token-findall', operation: 'findall', flags: [],
    pattern: '[a-z]+|[0-9]+', input: 'word 123 '.repeat(128) }
];
const startupPairs = [];
const evaluations = [];
const pageErrors = [];
let browser;
let browserVersion;
let userAgent;
let memory;
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
try {
  // Each pair starts a fresh browser process/context; warm uses a fresh document
  // and worker in that same context. No routes/interception (which disables cache).
  for (let pair = 0; pair < 5; pair++) {
    browser = await chromium.launch();
    browserVersion = browser.version();
    const context = await browser.newContext({ serviceWorkers: 'block', viewport: { width: 1280, height: 720 } });
    const phases = {};
    for (const phase of ['cold', 'warm']) {
      const page = await context.newPage();
      page.on('pageerror', error => pageErrors.push(String(error)));
      await page.goto(`http://127.0.0.1:${server.address().port}/`);
      await page.waitForFunction(() => window.performanceReady !== undefined);
      const ready = await page.evaluate(() => window.performanceReady);
      assert.equal(ready.versions.pyodide, config.pyodide);
      assert.equal(ready.versions.python, config.python);
      assert.equal(page.workers().length, 1);
      const resources = await page.workers()[0].evaluate(() =>
        performance.getEntriesByType('resource').map(row => ({ name: row.name,
          initiatorType: row.initiatorType, duration: row.duration,
          transferSize: row.transferSize, encodedBodySize: row.encodedBodySize,
          decodedBodySize: row.decodedBodySize, nextHopProtocol: row.nextHopProtocol,
          deliveryType: row.deliveryType ?? null })));
      phases[phase] = { ...ready, transfer: runtimeTransfer(resources, config.indexURL) };
      if (pair === 4 && phase === 'warm') {
        userAgent = await page.evaluate(() => navigator.userAgent);
        // Live worker timings: messaging + validation + compile/match + JSON.
        // Probe and workload setup are excluded; no warm-up samples discarded.
        for (const workload of workloads) {
          for (const mode of ['repeated-pattern', 'unique-pattern']) {
            const values = await page.evaluate(async ({ workload, mode }) => {
              const samples = [];
              let expected;
              for (let index = 0; index < 100; index++) {
                const row = { ...workload, pattern: workload.pattern +
                  (mode === 'unique-pattern' ? `(?#sample-${index})` : '') };
                const start = performance.now();
                const result = await window.performanceController.evaluate([row]);
                samples.push(performance.now() - start);
                const serialized = JSON.stringify(result.results[0]);
                if (index === 0) expected = serialized;
                if (serialized !== expected || !('result' in result.results[0])) {
                  throw new Error('Unstable workload result');
                }
                const value = result.results[0].result;
                if ((workload.id === 'log-search' && value?.groups[0] !== 'failed') ||
                    (workload.id === 'unicode-match' && value?.group !== workload.input) ||
                    (workload.id === 'token-findall' &&
                      (value?.length !== 256 || value[0] !== 'word' || value[1] !== '123'))) {
                  throw new Error('Incorrect workload result');
                }
              }
              return samples;
            }, { workload, mode });
            evaluations.push({ workload: workload.id, mode, milliseconds: distribution(values) });
          }
        }
        memory = await page.evaluate(() => ({
          method: 'performance.measureUserAgentSpecificMemory',
          secureContext: isSecureContext, crossOriginIsolated,
          available: typeof performance.measureUserAgentSpecificMemory === 'function',
          status: 'inconclusive', bytes: null,
          reason: 'Harness does not enable cross-origin isolation; no total-memory measurement. JS heap, WASM linear memory, and process RSS are not substituted.'
        }));
      }
      await page.close(); // Terminates this document's live worker before warm startup.
    }
    startupPairs.push({ pair: pair + 1, ...phases });
    await context.close();
    await browser.close();
    browser = null;
  }
  assert.deepEqual(pageErrors, []);
  const cold = distribution(startupPairs.map(row => row.cold.navigationToUsableMs));
  const warm = distribution(startupPairs.map(row => row.warm.navigationToUsableMs));
  const coldTransfer = startupPairs.map(row => row.cold.transfer);
  const warmCacheConfirmed = startupPairs.every(row => row.warm.transfer.allLocalCache);
  const transferMeasurable = coldTransfer.every(row => row.measurable && !row.allLocalCache);
  const status = (passes, measurable = true) => !measurable ? 'inconclusive' : passes ? 'pass' : 'fail';
  const evidenceFiles = ['performance.mjs', 'performance.html', 'performance-page.mjs',
    'performance-stats.mjs', 'controller.mjs', 'worker.mjs', 'evaluator.py', 'runtime.json'];
  const sourceSha256 = Object.fromEntries(await Promise.all(evidenceFiles.map(async name =>
    [name, createHash('sha256').update(await readFile(resolve(here, name))).digest('hex')])));
  console.log(JSON.stringify({ scope: 'issue42-bounded-desktop-performance-not-runtime-go',
    measuredAt: new Date().toISOString(), baseCommit: execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(),
    sourceSha256, versions: { ...config, chromium: browserVersion, node: process.version, playwright: '1.65.0' },
    device: { platform: os.platform(), release: os.release(), architecture: os.arch(),
      cpu: os.cpus()[0].model, logicalCpus: os.cpus().length, hostTotalMemoryBytes: os.totalmem(),
      osRelease: await readFile('/etc/os-release', 'utf8'), userAgent,
      mode: 'Headless desktop, 1280x720, no CPU/mobile emulation; shared host, load/power not controlled' },
    network: { runtime: config.indexURL, application: 'ephemeral HTTP loopback',
      conditions: 'Live HTTPS CDN, no network throttle or interception; host uplink, DNS, TLS, proxy/CDN caches and bandwidth not controlled or characterized' },
    definitions: {
      cold: 'New browser process and isolated context per pair; empty browser HTTP cache, not a guaranteed cold OS/DNS/CDN cache',
      warm: 'Fresh page and module worker in same primed context; previous page closed; CDN HTTP cache verified from worker Resource Timing, local harness files remain no-store',
      ready: 'Document navigation time origin through module fetch, controller import, worker creation, Pyodide load/version check, evaluator installation, and successful a+ search response; excludes browser launch, includes readiness probe, not production UI paint',
      evaluation: 'One case per request in an already-live worker; browser performance.now around controller.evaluate; repeated-pattern includes first compile then CPython re cache; unique-pattern adds a unique regex comment for each sample to avoid re cache; not isolated compiler timing',
      percentiles: 'Nearest rank ceil(p*n); all raw samples retained; 5 independent cold/warm pairs, 100 serial samples per workload/mode on final warm worker; no discarded outliers',
      transfer: 'Sum worker Resource Timing encodedBodySize for version-pinned runtime resources (compressed response bodies, not TLS/wire/header bytes). transferSize is browser-reported transfer with header-size accounting; cache hits can report zero. Missing/zero body sizes are inconclusive. Excludes local application assets.'
    },
    startup: { coldMilliseconds: cold, warmMilliseconds: warm, warmCacheConfirmed, pairs: startupPairs },
    workloads, evaluations, memory,
    desktopBudget: {
      coldReady: { targetMs: 5000, observedMaxMs: cold.max, status: status(cold.max <= 5000) },
      warmReady: { targetMs: 2000, observedMaxMs: warm.max, status: status(warm.max <= 2000, warmCacheConfirmed) },
      evaluation: { targetP95Ms: 100, status: status(evaluations.every(row => row.milliseconds.p95 <= 100)) },
      runtimeTransfer: { targetBytes: 15 * 1024 * 1024, status: status(coldTransfer.every(row => row.encodedBodyBytes <= 15 * 1024 * 1024), transferMeasurable) },
      memory: { targetBytes: 256 * 1024 * 1024, status: 'inconclusive' }
    },
    limitations: ['Small single-host desktop sample, not a population/SLA or controlled-network verdict',
      'No actual mobile device; every mobile budget remains inconclusive',
      'No total/peak browser memory verdict; no cross-origin-isolation deployment change',
      'No production integration, deployment/CDN guarantee, or runtime go/no-go',
      'Playwright Ubuntu fallback build on unsupported host OS; not supported-platform validation']
  }, null, 2));
} finally {
  await browser?.close();
  await new Promise(resolve => server.close(resolve));
}
