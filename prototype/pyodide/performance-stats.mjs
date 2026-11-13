export function distribution(samples) {
  if (!samples.length || samples.some(value => !Number.isFinite(value) || value < 0)) {
    throw new Error('Expected nonempty finite nonnegative samples');
  }
  const sorted = [...samples].sort((a, b) => a - b);
  const percentile = fraction => sorted[Math.ceil(fraction * sorted.length) - 1];
  return { n: samples.length, min: sorted[0], median: percentile(0.5),
    p95: percentile(0.95), max: sorted.at(-1), samples };
}

// Missing/opaque entries must not turn into a zero-byte budget pass.
export function runtimeTransfer(resources, indexURL) {
  const rows = resources.filter(row => row.name.startsWith(indexURL));
  const required = ['pyodide.mjs', 'pyodide.asm.mjs', 'pyodide.asm.wasm',
    'python_stdlib.zip', 'pyodide-lock.json'];
  const missing = required.filter(name => !rows.some(row => row.name === indexURL + name));
  const measurable = missing.length === 0 && rows.every(row => row.encodedBodySize > 0 && row.decodedBodySize > 0);
  return { resources: rows, missing, measurable,
    encodedBodyBytes: measurable ? rows.reduce((sum, row) => sum + row.encodedBodySize, 0) : null,
    reportedTransferBytes: measurable ? rows.reduce((sum, row) => sum + row.transferSize, 0) : null,
    allLocalCache: measurable && rows.every(row => row.transferSize === 0) };
}
