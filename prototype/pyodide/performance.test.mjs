import assert from 'node:assert/strict';
import test from 'node:test';
import { distribution, runtimeTransfer } from './performance-stats.mjs';

test('nearest-rank distributions retain all samples and reject missing observations', () => {
  const result = distribution(Array.from({ length: 100 }, (_, index) => 100 - index));
  assert.equal(result.p95, 95);
  assert.equal(result.median, 50);
  assert.equal(result.min, 1);
  assert.equal(result.max, 100);
  assert.equal(result.samples[0], 100);
  for (const samples of [[], [NaN], [-1], [Infinity]]) assert.throws(() => distribution(samples));
});

test('runtime transfer is inconclusive for missing/opaque resource sizes, not a free pass', () => {
  const base = 'https://example.test/runtime/';
  const rows = ['pyodide.mjs', 'pyodide.asm.mjs', 'pyodide.asm.wasm',
    'python_stdlib.zip', 'pyodide-lock.json'].map(name => ({
    name: base + name, encodedBodySize: 100, decodedBodySize: 200, transferSize: 400
  }));
  assert.equal(runtimeTransfer(rows, base).encodedBodyBytes, 500);
  assert.equal(runtimeTransfer(rows.slice(1), base).measurable, false);
  assert.equal(runtimeTransfer(rows.map(row => ({ ...row, encodedBodySize: 0 })), base).encodedBodyBytes, null);
  assert.equal(runtimeTransfer(rows.map(row => ({ ...row, transferSize: 0 })), base).allLocalCache, true);
  assert.equal(runtimeTransfer(rows, base).allLocalCache, false);
});
