// Structural comparison: object key order is not part of the JSON contract.
export function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value !== null && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])]));
  }
  return value;
}

export function equal(left, right) {
  return JSON.stringify(canonical(left)) === JSON.stringify(canonical(right));
}

export function compare(native, wasm, cases, python) {
  for (const result of [native, wasm]) {
    if (result.python !== python || result.implementation !== 'CPython') {
      throw new Error('Comparison requires exact same-version CPython');
    }
    if (!equal(result.results.map(row => row.id), cases.map(row => row.id))) {
      throw new Error('Missing, duplicated, or reordered case IDs');
    }
  }
  return cases.filter((_, i) => !equal(native.results[i], wasm.results[i])).map(row => row.id);
}

export function legacyDifferences(native, cases) {
  return cases.filter((row, i) => !equal(native.results[i], {
    id: row.id, ...(Object.hasOwn(row, 'error') ? { error: row.error } : { result: row.expected })
  })).map(row => row.id);
}

// Python spans count code points; JS slice counts UTF-16 code units.
export function slicePythonSpan(text, [start, end]) {
  if (start === -1 && end === -1) return null;
  return Array.from(text).slice(start, end).join('');
}
