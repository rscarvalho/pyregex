import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { compare, legacyDifferences } from './parity.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '../..');
const config = JSON.parse(await readFile(resolve(here, 'runtime.json')));
const fixtureBytes = await readFile(resolve(root, 'tests/fixtures/regex_baseline.json'));
const { engine_cases: cases } = JSON.parse(fixtureBytes);
const native = JSON.parse(execFileSync('docker', [
  'run', '--rm', '--network=none', '--read-only', '--cap-drop=ALL',
  '--security-opt=no-new-privileges', '--pids-limit=64', '--memory=256m',
  '--mount', `type=bind,src=${root},dst=/work,readonly`,
  config.nativeImage, 'python', '-B', '/work/prototype/pyodide/native.py'
], { encoding: 'utf8', timeout: 30000 }));
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
assert.equal(native.fixtureSha256, sha256(fixtureBytes));
assert.equal(native.evaluatorSha256, sha256(await readFile(resolve(here, 'evaluator.py'))));

// Ephemeral loopback port; no interaction with legacy ports 5000 or 8082.
const files = new Map([
  ['/', ['index.html', 'text/html']],
  ...['browser.mjs', 'worker.mjs', 'parity.mjs'].map(name => [`/${name}`, [name, 'text/javascript']]),
  ['/runtime.json', ['runtime.json', 'application/json']],
  ['/evaluator.py', ['evaluator.py', 'text/plain']]
]);
const server = createServer(async (req, res) => {
  const entry = files.get(req.url);
  if (!entry) { res.writeHead(404).end(); return; }
  try {
    res.writeHead(200, { 'Content-Type': entry[1], 'Cache-Control': 'no-store' });
    res.end(await readFile(resolve(here, entry[0])));
  } catch {
    res.destroy();
  }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
let browser;
try {
  browser = await chromium.launch();
  const page = await browser.newPage();
  page.setDefaultTimeout(70000);
  await page.goto(`http://127.0.0.1:${server.address().port}/`);
  const { versions, wasm, highlighted } = await page.evaluate(async cases => {
    const { runCases } = await import('./browser.mjs');
    return runCases(cases);
  }, cases);
  const mismatches = compare(native, wasm, cases, config.python);
  const legacy = legacyDifferences(native, cases);
  console.log(JSON.stringify({
    scope: 'issue42-first-unit-engine-parity-only',
    ...versions, browser: browser.version(), node: process.version,
    nativeImage: config.nativeImage,
    fixtureSha256: native.fixtureSha256, evaluatorSha256: native.evaluatorSha256,
    cases: cases.length, mismatches, legacyEngineDifferences: legacy,
    unicodeDisplay: highlighted,
    limitations: ['No production integration', 'No cancellation/recovery evidence',
      'No desktop/mobile performance or memory verdict', 'Bounded corpus, not exhaustive regex equivalence']
  }, null, 2));
  assert.deepEqual(mismatches, [], 'Native/WASM parity failed');
  assert.deepEqual(legacy, [], 'Review new differences from the 3.7 engine fixture expectations');
} finally {
  await browser?.close();
  await new Promise(resolve => server.close(resolve));
}
