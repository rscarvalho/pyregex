// Module worker: initialization, compilation and matching never run on the UI thread.
let runtime;
let ready;

async function initialize() {
  const response = await fetch('./runtime.json');
  if (!response.ok) throw new Error('Cannot fetch runtime pin');
  const config = await response.json();
  const { loadPyodide } = await import(`${config.indexURL}pyodide.mjs`);
  runtime = await loadPyodide({ indexURL: config.indexURL });
  if (runtime.version !== config.pyodide) throw new Error('Pyodide version mismatch');
  const source = await fetch('./evaluator.py');
  if (!source.ok) throw new Error('Cannot fetch evaluator');
  runtime.runPython(await source.text());
  const python = runtime.runPython('platform.python_version()');
  if (python !== config.python) throw new Error('CPython version mismatch');
  return { pyodide: runtime.version, python };
}

self.onmessage = async ({ data }) => {
  const { id, type, cases } = data;
  try {
    ready ??= initialize();
    const versions = await ready;
    if (type === 'init') {
      self.postMessage({ id, value: versions });
    } else if (type === 'evaluate') {
      // JSON is data, not interpolated Python source. Return a string, not PyProxy.
      runtime.globals.set('cases_json', JSON.stringify(cases));
      try {
        const value = JSON.parse(runtime.runPython('evaluate_json(cases_json)'));
        self.postMessage({ id, value });
      } finally {
        runtime.globals.delete('cases_json');
      }
    } else {
      throw new Error('Unknown worker request');
    }
  } catch (error) {
    // Infrastructure failures must not masquerade as regex error categories.
    self.postMessage({ id, failure: String(error) });
  }
};
