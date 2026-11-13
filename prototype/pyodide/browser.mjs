import { slicePythonSpan } from './parity.mjs';
import { RegexController } from './controller.mjs';

export async function runCases(cases) {
  const controller = new RegexController();
  try {
    const versions = await controller.start();
    const wasm = await controller.evaluate(cases);
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
    controller.close();
  }
}
