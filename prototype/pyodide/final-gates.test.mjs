import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { distribution } from './performance-stats.mjs';

const evidence = JSON.parse(await readFile(new URL('./evidence/final-gates.json', import.meta.url)));
const partialMemory = JSON.parse(await readFile(new URL('./evidence/memory-cdp.json', import.meta.url)));

test('final-gates evidence identifies the exact current measurement sources', async () => {
  for (const artifact of [evidence, partialMemory]) {
    for (const [name, expected] of Object.entries(artifact.sourceSha256)) {
      const bytes = await readFile(new URL(name, import.meta.url));
      assert.equal(createHash('sha256').update(bytes).digest('hex'), expected, name);
    }
  }
  assert.deepEqual(evidence.pageErrors, []);
  assert.equal(evidence.versions.python, '3.14.2');
  assert.equal(evidence.versions.pyodide, '314.0.7');
});

test('network summaries retain every sample, unchanged targets and actual worker configuration', () => {
  assert.equal(evidence.networkProfiles.length, 2);
  for (const [index, row] of evidence.networkProfiles.entries()) {
    assert.equal(row.pairs.length, 2);
    assert.deepEqual(row.profile.targets, index === 0 ?
      { coldMs: 5000, warmMs: 2000 } : { coldMs: 10000, warmMs: 4000 });
    for (const phase of ['cold', 'warm']) {
      const samples = row.pairs.map(pair => pair[phase]);
      if (samples.every(sample => Number.isFinite(sample.navigationToUsableMs))) {
        assert.deepEqual(row.summary[phase].milliseconds,
          distribution(samples.map(sample => sample.navigationToUsableMs)));
      } else assert.equal(row.summary[phase].status, 'inconclusive');
      if (row.summary[phase].status !== 'inconclusive') {
        assert.equal(row.summary[phase].cacheVerified, true);
        assert.equal(row.summary[phase].networkConfigured, true);
      }
    }
  }
});

test('memory snapshots never imply total/peak memory or actual mobile approval', () => {
  assert.equal(evidence.memory.targetBytes, 256 * 1024 * 1024);
  assert.equal(evidence.memory.gateStatus, 'inconclusive');
  assert.equal(evidence.memory.samples.length, 2);
  assert.equal(partialMemory.gateStatus, 'inconclusive');
  assert.equal(partialMemory.method, 'CDP Runtime.getHeapUsage');
  for (const sample of evidence.memory.samples) {
    assert.equal(sample.secureContext, true);
    assert.equal(sample.crossOriginIsolated, true);
    assert.ok(['measured', 'unsupported', 'failed', 'watchdog-expired'].includes(sample.status));
    if (sample.status === 'measured') assert.ok(Number.isFinite(sample.value.bytes) && sample.value.bytes > 0);
  }
});
