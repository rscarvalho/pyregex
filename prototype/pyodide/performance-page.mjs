import { RegexController } from './controller.mjs';

// Separate from the diagnostic UI: automatic navigation-to-usable-runtime boundary.
window.performanceController = new RegexController();
window.performanceReady = (async () => {
  const start = performance.now();
  const versions = await window.performanceController.start();
  const initializedMs = performance.now();
  const result = await window.performanceController.evaluate([
    { id: 'ready', operation: 'search', flags: [], pattern: 'a+', input: 'baaa' }
  ]);
  if (result.results[0].result.group !== 'aaa') throw new Error('Readiness probe failed');
  const usableMs = performance.now();
  document.querySelector('output').textContent = 'Ready';
  return { versions, navigationToUsableMs: usableMs,
    moduleStartMs: start, controllerStartupMs: initializedMs - start,
    readinessProbeMs: usableMs - initializedMs };
})();
// Keep errors observable to the runner even if initialization rejects before it attaches.
window.performanceReady.catch(() => {});
