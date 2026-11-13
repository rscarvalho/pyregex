import assert from 'node:assert/strict';
import test from 'node:test';
import { RegexController } from './controller.mjs';
import { LIMITS, validateCases } from './limits.mjs';

const row = { id: 'test', operation: 'match', flags: [], pattern: 'a', input: 'a' };
function harness() {
  let time = 0;
  const workers = [], timers = [];
  const controller = new RegexController({
    now: () => time,
    schedule: (callback, ms) => { const timer = { callback, ms }; timers.push(timer); return timer; },
    unschedule: timer => { timer.cleared = true; },
    createWorker: () => {
      const worker = { messages: [], terminated: false,
        postMessage(data) { this.messages.push(data); },
        terminate() { this.terminated = true; },
        respond(value, request = this.messages.at(-1)) {
          this.onmessage({ data: { id: request.id, generation: request.generation, value } });
        } };
      workers.push(worker);
      return worker;
    }
  });
  return { controller, workers, timers, clock: value => { time = value; },
    async ready() { const startup = controller.start(); workers.at(-1).respond({ python: '3.14.2' }); await startup; } };
}

test('silent compile OR match is bounded by the same main-thread deadline; recovery rejects stale races', async () => {
  const h = harness();
  await h.ready();
  for (let i = 0; i < 3; i++) {
    const old = h.workers.at(-1);
    const result = h.controller.evaluate([row]);
    const rejected = assert.rejects(result, /Evaluation timeout/);
    const oldRequest = old.messages.at(-1);
    const timer = h.timers.at(-1);
    assert.equal(timer.ms, LIMITS.evaluationMs);
    // No phase/compile acknowledgement needed: silence from either phase is contained.
    h.clock((i + 1) * 2000);
    if (i % 2) timer.callback();
    else old.respond('late result'); // Result at deadline before timer must still time out.
    await rejected;
    assert.ok(old.terminated);
    const current = h.workers.at(-1);
    old.respond('stale success', oldRequest);
    old.onerror({ message: 'stale error' });
    timer.callback(); // Already-queued timer must not kill replacement.
    assert.equal(current.terminated, false);
    current.respond('ready');
    await h.controller.start();
    const next = h.controller.evaluate([row]);
    const nextRequest = current.messages.at(-1);
    current.respond('wrong id', { ...nextRequest, id: oldRequest.id });
    current.respond('wrong generation', { ...nextRequest, generation: oldRequest.generation });
    assert.ok(h.controller.pending);
    current.respond('normal');
    assert.equal(await next, 'normal');
  }
  h.controller.close();
});

test('cancel wins once, queue is bounded, close rejects and never resurrects', async () => {
  const h = harness();
  await h.ready();
  const result = h.controller.evaluate([row]);
  await assert.rejects(h.controller.evaluate([row]), /busy/);
  const rejected = assert.rejects(result, /Cancelled/);
  const old = h.workers[0];
  assert.equal(h.controller.cancel(), true);
  old.respond('late');
  await rejected;
  const startup = h.controller.start();
  const closed = assert.rejects(startup, /closed/);
  h.controller.close();
  await closed;
  h.workers.at(-1).respond('late ready');
  assert.equal(h.controller.cancel(), false);
  await assert.rejects(h.controller.start(), /closed/);
  await assert.rejects(h.controller.evaluate([row]), /closed/);
});

test('startup deadline is separate and does not loop; worker failures are terminal but retryable', async () => {
  const h = harness();
  const startup = h.controller.start();
  const rejected = assert.rejects(startup, /Startup timeout/);
  assert.equal(h.timers[0].ms, 30000);
  h.timers[0].callback();
  await rejected;
  assert.equal(h.workers.length, 1);
  await h.ready();
  const result = h.controller.evaluate([row]);
  const failed = assert.rejects(result, /decoding/);
  h.workers.at(-1).onmessageerror();
  await failed;
  assert.ok(h.workers.at(-1).terminated);
  await h.ready();
  h.controller.close();
});

test('success before deadline wins over queued timer; validation bounds only fixture data', async () => {
  const h = harness();
  await h.ready();
  const result = h.controller.evaluate([row]);
  const timer = h.timers.at(-1);
  h.clock(1999);
  h.workers.at(-1).respond('ok');
  timer.callback();
  assert.equal(await result, 'ok');
  assert.equal(h.workers.length, 1);
  for (const cases of [[], Array(33).fill(row), [{ ...row, source: 'while True: pass' }],
    [{ ...row, pattern: 'a'.repeat(1025) }], [{ ...row, input: 'a'.repeat(8193) }],
    Array(5).fill({ ...row, input: 'a'.repeat(8192) })]) {
    assert.throws(() => validateCases(cases));
  }
  assert.deepEqual(validateCases([{ ...row, expected: 'ignored' }]), [row]);
  await assert.rejects(h.controller.evaluate([{ ...row, operation: 'exec' }]), /Invalid/);
  assert.equal(h.controller.pending, null);
  h.controller.close();
});

test('worker construction failure rejects startup instead of escaping recovery', async () => {
  const controller = new RegexController({ createWorker: () => { throw new Error('creation failed'); } });
  await assert.rejects(controller.start(), /creation failed/);
  assert.equal(controller.pending, undefined);
  controller.close();
});
