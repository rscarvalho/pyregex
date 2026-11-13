import assert from 'node:assert/strict';

// Playwright interactions with the tiny harness, not arbitrary Python execution.
export async function runRecovery(page) {
  await page.evaluate(async () => { window.recoveryState = (await import('./ui.mjs')).state; });
  const state = () => page.evaluate(() => window.recoveryState);
  const ready = () => page.waitForFunction(() => window.recoveryState.phase === 'ready');
  const fill = row => page.getByRole('textbox', { name: 'Cases' }).fill(JSON.stringify([row]));
  const normal = { id: 'normal', operation: 'search', flags: [], pattern: 'a+', input: 'baaa' };
  const pathological = { ...normal, id: 'pathological-match', pattern: '(a+)+$', input: 'a'.repeat(128) + '!' };
  await page.locator('#start').click();
  await ready();
  const cycles = [];
  for (let i = 0; i < 3; i++) {
    for (const mode of ['timeout', 'cancel']) {
      await fill(pathological);
      const before = await state();
      const beatIndex = before.beats.length;
      await page.locator('#run').click();
      await page.waitForFunction(() => window.recoveryState.phase === 'running');
      if (mode === 'cancel') {
        // Give the real synchronous Python match time to enter its pathological work.
        await page.waitForTimeout(150);
        await page.locator('#cancel').click();
      }
      await page.waitForFunction(count => window.recoveryState.events.length > count, before.events.length);
      const acknowledged = await state();
      const event = acknowledged.events[before.events.length];
      assert.equal(event.type, mode === 'timeout' ? 'Evaluation timeout' : 'Cancelled');
      const ackMs = mode === 'timeout' ? event.ms - 2000 : event.cancelAckMs;
      assert.ok(ackMs >= 0 && ackMs <= 250, `Acknowledgement ${ackMs} ms`);
      await ready();
      const recreated = await state();
      assert.ok(recreated.generation > before.generation);
      await fill(normal);
      const count = recreated.events.length;
      await page.locator('#run').click();
      await page.waitForFunction(count => window.recoveryState.events.length > count, count);
      const after = await state();
      const result = after.events[count];
      assert.equal(result.type, 'result');
      assert.equal(result.result.results[0].result.group, 'aaa');
      const beats = after.beats.slice(Math.max(0, beatIndex - 1));
      const maxHeartbeatGapMs = Math.max(...beats.slice(1).map((beat, index) => beat - beats[index]));
      assert.ok(beats.length > 2 && maxHeartbeatGapMs <= 250, `Heartbeat gap ${maxHeartbeatGapMs} ms`);
      cycles.push({ cycle: i + 1, mode, evaluationMs: event.ms, acknowledgementMs: ackMs,
        recreatedGeneration: recreated.generation,
        startupMs: recreated.events.findLast(event => event.type === 'ready').ms,
        nextEvaluationMs: result.ms, maxHeartbeatGapMs });
    }
  }
  return { initialStartupMs: (await state()).events[0].ms, cycles,
    pathological: { pattern: pathological.pattern, input: '128 ASCII a followed by !' },
    acknowledgementTargetMs: 250, heartbeatIntervalMs: 20,
    limitations: ['Single headless desktop Chromium on this host; no mobile/performance verdict',
      'Heartbeat measures main-thread timer/DOM updates, not compositor paint or physical input latency',
      'Cancellation acknowledgement starts at DOM click handler, not external input delivery',
      'Startup/recreation is measured separately and is not required to finish within 250 ms',
      'No deterministic real compile hang exercised; compile containment tested with fake worker silence',
      'Output cap applies after Python result allocation; not a hard memory sandbox'] };
}
