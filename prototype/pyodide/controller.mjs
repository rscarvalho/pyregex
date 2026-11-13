import { LIMITS, validateCases } from './limits.mjs';

// One in-flight operation; no queue. Dependencies are injectable only in Node tests.
export class RegexController {
  constructor({ createWorker = () => new Worker('./worker.mjs', { type: 'module' }),
    now = () => performance.now(), schedule = (callback, ms) => setTimeout(callback, ms),
    unschedule = timer => clearTimeout(timer) } = {}) {
    Object.assign(this, { createWorker, now, schedule, unschedule });
    this.generation = 0;
    this.nextId = 0;
    this.closed = false;
    this.ready = false;
  }

  start() {
    if (this.closed) return Promise.reject(new Error('Controller closed'));
    if (this.worker) return this.startup;
    this.ready = false;
    const generation = ++this.generation;
    let worker;
    try { worker = this.worker = this.createWorker(); }
    catch (error) {
      this.startup = Promise.reject(error);
      this.startup.catch(() => {});
      return this.startup;
    }
    worker.onmessage = ({ data }) => {
      const pending = this.pending;
      if (this.worker !== worker || generation !== this.generation ||
          !pending || data.generation !== generation || data.id !== pending.id) return;
      // A queued result does not win merely because the timer callback is delayed.
      if (this.now() >= pending.deadline) { this.expire(pending); return; }
      if (data.failure) { this.breakWorker(new Error(data.failure)); return; }
      this.pending = null;
      this.unschedule(pending.timer);
      if (pending.type === 'init') this.ready = true;
      pending.resolve(data.value);
    };
    worker.onerror = event => {
      if (this.worker === worker) this.breakWorker(new Error(event.message));
    };
    worker.onmessageerror = () => {
      if (this.worker === worker) this.breakWorker(new Error('Worker message decoding failed'));
    };
    this.startup = this.request('init', {}, LIMITS.startupMs);
    // Automatic recovery can fail with no consumer currently awaiting startup.
    this.startup.catch(() => {});
    return this.startup;
  }

  evaluate(cases) {
    if (this.closed || !this.ready || this.pending) {
      return Promise.reject(new Error(this.closed ? 'Controller closed' : 'Not ready or busy; no queue'));
    }
    try { return this.request('evaluate', { cases: validateCases(cases) }, LIMITS.evaluationMs); }
    catch (error) { return Promise.reject(error); }
  }

  request(type, payload, duration) {
    return new Promise((resolve, reject) => {
      const pending = { id: ++this.nextId, type, resolve, reject, deadline: this.now() + duration };
      this.pending = pending;
      pending.timer = this.schedule(() => {
        if (this.pending === pending) this.expire(pending);
      }, duration);
      try { this.worker.postMessage({ id: pending.id, generation: this.generation, type, ...payload }); }
      catch (error) { this.breakWorker(error); }
    });
  }

  expire(pending) {
    this.breakWorker(new Error(pending.type === 'init' ? 'Startup timeout' : 'Evaluation timeout'),
      pending.type === 'evaluate');
  }

  breakWorker(error, restart = false) {
    const pending = this.pending;
    this.pending = null;
    this.ready = false;
    const worker = this.worker;
    this.worker = null; // Invalidate before terminate or promise callbacks.
    worker?.terminate();
    if (pending) {
      this.unschedule(pending.timer);
      pending.reject(error);
    }
    if (restart && !this.closed) this.start();
  }

  cancel() {
    if (!this.pending) return false;
    this.breakWorker(new Error('Cancelled'), true);
    return true;
  }

  close() {
    this.closed = true;
    this.breakWorker(new Error('Controller closed'));
  }
}
