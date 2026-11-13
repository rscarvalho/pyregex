import assert from 'node:assert/strict';
import test from 'node:test';
import { compare, equal, legacyDifferences, slicePythonSpan } from './parity.mjs';

const cases = [{ id: 'a', expected: [] }, { id: 'b', error: 'invalid_pattern' }];
const result = () => ({ python: '3.14.2', implementation: 'CPython', results: [
  { id: 'a', result: [] }, { id: 'b', error: 'invalid_pattern' }
] });

test('compare structure, categories and case coverage; never ignore drift', () => {
  assert.ok(equal({ b: 1, a: [] }, { a: [], b: 1 }));
  assert.ok(!equal([], null));
  assert.deepEqual(compare(result(), result(), cases, '3.14.2'), []);
  const changed = result();
  changed.results[0].result = null;
  assert.deepEqual(compare(result(), changed, cases, '3.14.2'), ['a']);
  changed.results[1].error = 'invalid_flags';
  assert.deepEqual(compare(result(), changed, cases, '3.14.2'), ['a', 'b']);
  assert.deepEqual(legacyDifferences(changed, cases), ['a', 'b']);
  assert.throws(() => compare(result(), { ...result(), python: '3.14.7' }, cases, '3.14.2'));
  assert.throws(() => compare(result(), { ...result(), results: [] }, cases, '3.14.2'));
  assert.throws(() => compare(result(), { ...result(), results: [result().results[0], result().results[0]] }, cases, '3.14.2'));
});

test('display Python code-point spans without Unicode normalization', () => {
  assert.equal(slicePythonSpan('😀xé😀é!', [2, 6]), 'é😀é');
  assert.equal(slicePythonSpan('😀x', [1, 1]), '');
  assert.equal(slicePythonSpan('😀x', [-1, -1]), null);
});
