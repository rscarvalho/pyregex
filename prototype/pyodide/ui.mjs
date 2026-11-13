import { RegexController } from './controller.mjs';

const controller = new RegexController();
const status = document.querySelector('#status');
const sample = { id: 'normal', operation: 'search', flags: [], pattern: 'a+', input: 'baaa' };
document.querySelector('textarea').value = JSON.stringify([sample]);
export const state = { phase: 'idle', events: [], beats: [], generation: 0 };
function record(event) {
  state.events.push(event);
  if (state.events.length > 32) state.events.shift();
}
setInterval(() => {
  state.beats.push(performance.now());
  if (state.beats.length > 10000) state.beats.shift();
  document.querySelector('#heartbeat').textContent = String(state.beats.length);
}, 20);
function phase(value) {
  state.phase = value;
  state.generation = controller.generation;
  status.textContent = value;
}
async function start() {
  phase('starting');
  const begin = performance.now();
  try {
    await controller.start();
    record({ type: 'ready', ms: performance.now() - begin, generation: controller.generation });
    phase('ready');
  } catch (error) { phase(error.message); }
}
document.querySelector('#start').onclick = () => {
  if (!['running', 'starting'].includes(state.phase)) return start();
};
document.querySelector('#cancel').onclick = () => {
  if (state.phase !== 'running') return;
  state.cancelAt = performance.now();
  controller.cancel();
};
document.querySelector('#run').onclick = async () => {
  if (state.phase !== 'ready') return;
  const begin = performance.now();
  phase('running');
  try {
    const input = document.querySelector('textarea').value;
    if (input.length > 65536) throw new Error('UI JSON limit exceeded');
    const result = await controller.evaluate(JSON.parse(input));
    document.querySelector('#result').textContent = JSON.stringify(result);
    record({ type: 'result', ms: performance.now() - begin, result });
    phase('ready');
  } catch (error) {
    const at = performance.now();
    document.querySelector('#result').textContent = error.message;
    record({ type: error.message, ms: at - begin,
      cancelAckMs: error.message === 'Cancelled' ? at - state.cancelAt : null });
    if (error.message === 'Evaluation timeout' || error.message === 'Cancelled') await start();
    else phase(controller.ready ? 'ready' : 'failed');
  }
};
addEventListener('pagehide', () => controller.close());
