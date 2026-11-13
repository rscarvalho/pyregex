import { slicePythonSpan } from './parity.mjs';

export async function runCases(cases) {
  const worker = new Worker('./worker.mjs', { type: 'module' });
  let nextId = 0;
  const pending = new Map();
  const fail = error => {
    for (const { reject } of pending.values()) reject(error);
    pending.clear();
  };
  worker.onmessage = ({ data }) => {
    const request = pending.get(data.id);
    if (!request) return;
    pending.delete(data.id);
    if (data.failure) request.reject(new Error(data.failure));
    else request.resolve(data.value);
  };
  worker.onerror = event => fail(new Error(event.message));
  worker.onmessageerror = () => fail(new Error('Worker message decoding failed'));
  const request = (type, payload = {}) => new Promise((resolve, reject) => {
    const id = ++nextId;
    pending.set(id, { resolve, reject });
    worker.postMessage({ id, type, ...payload });
  });
  // Harness watchdog only, NOT the issue #42 two-second per-evaluation deadline.
  const watchdog = setTimeout(() => {
    worker.terminate();
    fail(new Error('Harness exceeded 60 seconds'));
  }, 60000);
  try {
    const versions = await request('init');
    const wasm = await request('evaluate', { cases });
    const unicode = cases.find(row => row.id === 'unicode-offsets');
    const result = wasm.results.find(row => row.id === unicode.id).result;
    const highlighted = slicePythonSpan(unicode.input, result.span);
    // Exercise an actual DOM text boundary without inserting untrusted HTML.
    document.querySelector('output').textContent = highlighted;
    if (document.querySelector('output').textContent !== result.group) {
      throw new Error('Code-point span display mismatch');
    }
    return { versions, wasm, highlighted };
  } finally {
    clearTimeout(watchdog);
    worker.terminate();
    fail(new Error('Harness closed'));
  }
}
