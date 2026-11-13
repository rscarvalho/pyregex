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
const sourceFiles = ['final-gates.mjs', 'performance.html', 'performance-page.mjs',
  'performance-stats.mjs', 'controller.mjs', 'limits.mjs', 'worker.mjs',
  'runtime.json', 'evaluator.py', 'package-lock.json'];
const sourceSha256 = Object.fromEntries(await Promise.all(sourceFiles.map(async name =>
  [name, createHash('sha256').update(await readFile(resolve(here, name))).digest('hex')])));
const allowed = new Map([
  ['/', ['performance.html', 'text/html']],
  ...['performance-page.mjs', 'controller.mjs', 'limits.mjs', 'worker.mjs'].map(name =>
    [`/${name}`, [name, 'text/javascript']]),
  ['/runtime.json', ['runtime.json', 'application/json']],
  ['/evaluator.py', ['evaluator.py', 'text/plain']]
]);
let isolated = false;
const server = createServer(async (req, res) => {
  const entry = allowed.get(req.url);
  if (!entry) { res.writeHead(404).end(); return; }
  try {
    res.writeHead(200, { 'Content-Type': entry[1], 'Cache-Control': 'no-store',
      ...(isolated ? { 'Cross-Origin-Opener-Policy': 'same-origin',
        'Cross-Origin-Embedder-Policy': 'require-corp' } : {}) });
    res.end(await readFile(resolve(here, entry[0])));
  } catch { res.destroy(); }
});
// Host watchdog remains effective even when page timers stop progressing.
const watchdog = setTimeout(() => { console.error('Final-gates 240 s watchdog'); process.exit(2); }, 240_000);
const profiles = [
  { id: 'controlled-desktop', cpuRate: 1, latency: 40,
    downloadThroughput: 2_500_000, uploadThroughput: 625_000,
    viewport: { width: 1280, height: 720 }, isMobile: false, hasTouch: false,
    targets: { coldMs: 5000, warmMs: 2000 } },
  { id: 'mobile-emulated-not-real-device', cpuRate: 4, latency: 100,
    downloadThroughput: 500_000, uploadThroughput: 125_000,
    viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true,
    targets: { coldMs: 10000, warmMs: 4000 } }
];
const errors = [];
const results = [];
let browser;
let browserVersion;

// Non-flat sessions are documented but deprecated. They let this bounded runner
// configure each worker BEFORE execution; no guessing that page settings inherit.
async function configure(page, profile) {
  const cdp = await page.context().newCDPSession(page);
  const attempts = [];
  let nextId = 0;
  const pending = new Map();
  cdp.on('Target.receivedMessageFromTarget', ({ sessionId, message }) => {
    const row = JSON.parse(message);
    const key = `${sessionId}:${row.id}`;
    const entry = pending.get(key);
    if (entry) {
      clearTimeout(entry.timer);
      pending.delete(key);
      row.error ? entry.reject(new Error(JSON.stringify(row.error))) : entry.resolve(row.result);
    }
  });
  const sendWorker = (sessionId, method, params = {}) => new Promise((resolve, reject) => {
    const id = ++nextId;
    const key = `${sessionId}:${id}`;
    const timer = setTimeout(() => { pending.delete(key); reject(new Error(`${method} watchdog`)); }, 3000);
    pending.set(key, { resolve, reject, timer });
    cdp.send('Target.sendMessageToTarget', { sessionId, message: JSON.stringify({ id, method, params }) },
      { timeout: 3000 }).catch(error => {
      clearTimeout(timer); pending.delete(key); reject(error);
    });
  });
  const conditions = { urlPattern: '', latency: profile.latency,
    downloadThroughput: profile.downloadThroughput, uploadThroughput: profile.uploadThroughput };
  await cdp.send('Network.enable', {}, { timeout: 3000 });
  await cdp.send('Network.emulateNetworkConditionsByRule', { matchedNetworkConditions: [conditions] }, { timeout: 3000 });
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: profile.cpuRate }, { timeout: 3000 });
  cdp.on('Target.attachedToTarget', ({ sessionId, targetInfo }) => {
    if (targetInfo.type !== 'worker') return;
    const attempt = { type: targetInfo.type, network: null, cpu: null };
    attempts.push(attempt);
    (async () => {
      for (const [key, method, params] of [
        ['network', 'Network.emulateNetworkConditionsByRule', { matchedNetworkConditions: [conditions] }],
        ['cpu', 'Emulation.setCPUThrottlingRate', { rate: profile.cpuRate }]
      ]) {
        try { await sendWorker(sessionId, method, params); attempt[key] = { status: 'accepted' }; }
        catch (error) { attempt[key] = { status: 'unsupported-or-failed', error: String(error) }; }
      }
      await sendWorker(sessionId, 'Runtime.runIfWaitingForDebugger');
    })().catch(error => errors.push(String(error)));
  });
  await cdp.send('Target.setAutoAttach', { autoAttach: true, waitForDebuggerOnStart: true, flatten: false }, { timeout: 3000 });
  return attempts;
}

async function readyPage(context) {
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(String(error)));
  return page;
}
async function navigate(page) {
  await page.goto(`http://127.0.0.1:${server.address().port}/`, { timeout: 35000 });
  await page.waitForFunction(() => window.performanceReady !== undefined, null, { timeout: 35000 });
  const ready = await page.evaluate(() => window.performanceReady);
  assert.equal(ready.versions.pyodide, config.pyodide);
  assert.equal(ready.versions.python, config.python);
  assert.equal(page.workers().length, 1);
  const resources = await page.workers()[0].evaluate(() => performance.getEntriesByType('resource').map(row => ({
    name: row.name, duration: row.duration, startTime: row.startTime, responseEnd: row.responseEnd,
    transferSize: row.transferSize, encodedBodySize: row.encodedBodySize, decodedBodySize: row.decodedBodySize
  })));
  return { ...ready, transfer: runtimeTransfer(resources, config.indexURL) };
}

await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
try {
  // Memory is separate: headers enabled only here, no CPU/network emulation.
  isolated = true;
  browser = await chromium.launch();
  browserVersion = browser.version();
  const context = await browser.newContext({ serviceWorkers: 'block' });
  const page = await readyPage(context);
  const cdnResponses = [];
  page.on('response', response => {
    if (response.url().startsWith(config.indexURL)) {
      const headers = response.headers();
      cdnResponses.push({ url: response.url(), status: response.status(),
        accessControlAllowOrigin: headers['access-control-allow-origin'] ?? null,
        crossOriginResourcePolicy: headers['cross-origin-resource-policy'] ?? null });
    }
  });
  const memoryReady = await navigate(page);
  const memory = { ready: memoryReady, cdnResponses, samples: [],
    targetBytes: 256 * 1024 * 1024, gateStatus: 'inconclusive',
    meaning: 'Implementation-specific whole-web-app estimates including worker; not process RSS, peak usage, allocation limit, or production isolation validation' };
  for (const phase of ['after-ready', 'after-100-probes']) {
    if (phase === 'after-100-probes') await page.evaluate(async () => {
      for (let i = 0; i < 100; i++) {
        const result = await window.performanceController.evaluate([
          { id: 'memory-probe', operation: 'search', flags: [], pattern: 'a+', input: 'baaa' }
        ]);
        if (result.results[0].result.group !== 'aaa') throw new Error('Memory workload failed');
      }
    });
    // No force-GC flags. API can wait for GC; 12 s max each, not indefinite.
    memory.samples.push({ phase, ...await page.evaluate(async () => {
      const constraints = { secureContext: isSecureContext, crossOriginIsolated,
        available: typeof performance.measureUserAgentSpecificMemory === 'function' };
      if (!constraints.available) return { ...constraints, status: 'unsupported' };
      let timer;
      const start = performance.now();
      try {
        return { ...constraints, ...await Promise.race([
          performance.measureUserAgentSpecificMemory().then(value => ({ status: 'measured', value })),
          new Promise(resolve => { timer = setTimeout(() => resolve({ status: 'watchdog-expired' }), 12000); })
        ]), elapsedMs: performance.now() - start };
      } catch (error) { return { ...constraints, status: 'failed', error: String(error), elapsedMs: performance.now() - start }; }
      finally { clearTimeout(timer); }
    }) });
  }
  await browser.close(); browser = null;
  isolated = false;
  for (const profile of profiles) {
    const pairs = [];
    for (let pair = 0; pair < 2; pair++) {
      browser = await chromium.launch();
      const context = await browser.newContext({ serviceWorkers: 'block',
        viewport: profile.viewport, isMobile: profile.isMobile, hasTouch: profile.hasTouch });
      const phases = {};
      for (const phase of ['cold', 'warm']) {
        const page = await readyPage(context);
        const workerConfiguration = await configure(page, profile);
        try { phases[phase] = { ...await navigate(page), workerConfiguration }; }
        catch (error) { phases[phase] = { status: 'startup-failed', error: String(error), workerConfiguration }; }
        await page.close();
      }
      pairs.push({ pair: pair + 1, ...phases });
      await browser.close(); browser = null;
    }
    const summary = Object.fromEntries(['cold', 'warm'].map(phase => {
      const samples = pairs.map(row => row[phase]);
      const complete = samples.every(row => Number.isFinite(row.navigationToUsableMs));
      const cacheVerified = samples.every(row => row.transfer?.measurable &&
        (phase === 'warm' ? row.transfer.allLocalCache : !row.transfer.allLocalCache));
      const networkConfigured = samples.every(row => row.workerConfiguration.length === 1 &&
        row.workerConfiguration[0].network?.status === 'accepted');
      const workerCPUConfigured = samples.every(row => row.workerConfiguration.length === 1 &&
        row.workerConfiguration[0].cpu?.status === 'accepted');
      return [phase, { milliseconds: complete ? distribution(samples.map(row => row.navigationToUsableMs)) : null,
        targetMs: profile.targets[`${phase}Ms`], cacheVerified, networkConfigured, workerCPUConfigured,
        status: !complete || !cacheVerified || !networkConfigured ? 'inconclusive' :
          samples.every(row => row.navigationToUsableMs <= profile.targets[`${phase}Ms`]) ? 'pass-in-sample' : 'fail-in-sample' }];
    }));
    results.push({ profile, pairs, summary });
  }
  assert.deepEqual(errors, []);
  // Only ephemeral loopback origins are sanitized; raw numerical observations retained.
  const evidence = { scope: 'issue42-final-bounded-diagnostics-not-production',
    measuredAt: new Date().toISOString(), baseCommit: execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(),
    sourceSha256, versions: { ...config, chromium: browserVersion, playwright: '1.65.0', node: process.version },
    device: { cpu: os.cpus()[0].model, logicalCpus: os.cpus().length, platform: os.platform(),
      release: os.release(), architecture: os.arch(), hostRAMBytes: os.totalmem() },
    definitions: { ready: 'Unchanged performance-page navigation time origin through successful a+ probe',
      samples: 'Two cold/warm pairs per profile, fresh browser per pair; no outlier removal; nearest-rank p95=max at n=2',
      network: 'CDP Network.emulateNetworkConditionsByRule global rule on page and explicitly paused worker; separate per-target throughput caps, live CDN and host link can be slower; not a physical shared-link simulation',
      cpu: 'CDP Emulation.setCPUThrottlingRate on page; worker attempt and actual support recorded, never assumed inherited',
      memory: 'Two sequential API requests with 12 s browser watchdog each; 240 s host watchdog overall; no forced GC or browser security flags',
      isolation: 'COOP same-origin and COEP require-corp only on separate memory-harness allowlisted responses; no CSP changes anywhere',
      limitations: 'No real mobile, no mobile thermal/ARM/power model; unsupported-host Playwright Ubuntu fallback; host CPU/load/power and uplink uncontrolled; emulation instrumentation adds startup overhead; no SLA or total/peak memory pass' },
    memory, networkProfiles: results, pageErrors: errors };
  console.log(JSON.stringify(evidence, null, 2).replaceAll(/http:\/\/127\.0\.0\.1:\d+/g, 'http://127.0.0.1:PORT'));
} finally {
  clearTimeout(watchdog);
  await browser?.close();
  await new Promise(resolve => server.close(resolve));
}
