# Issue #42: bounded parity and worker-recovery prototype

Standalone experiment for [#42](https://github.com/rscarvalho/pyregex/issues/42),
under the [#41](https://github.com/rscarvalho/pyregex/issues/41) runtime gate.
**Not production integration and not completion of #42.** No application imports,
Flask requests, legacy asset tooling, or JavaScript replacement regex engine.

## Scope and timebox

The agreed overall prototype timebox is **five engineer-days total**, including
the **half-day legacy setup (already done)**. The first unit established engine
parity; the next adds bounded worker recovery. Neither extends that timebox.
Initial agreed targets for the later measured gate:

| Metric | Desktop | Mobile |
| --- | --- | --- |
| Cold ready | 5 s | 10 s |
| Warm ready | 2 s | 4 s |
| Ordinary evaluation p95 | 100 ms | 250 ms |
| Compressed runtime transfer | 15 MiB | 15 MiB |
| Evaluation timeout | 2 s | 2 s |
| UI recovery after timeout | 250 ms | 250 ms |
| Memory, where measurable | 256 MiB | 256 MiB |

These are **targets, not measurements or a performance verdict**. No actual
mobile evidence exists in this unit. Define devices, network/cache conditions,
ordinary workload, sample count, readiness boundaries and memory method before
measuring. The native container's 256 MiB safety limit is not a browser-memory
measurement. The controller now owns a 2 s evaluation deadline, separate from
its 30 s startup safety bound (not the startup performance target).

## Pins and fresh documentation

`runtime.json` pins Pyodide **314.0.7**, bundled CPython **3.14.2**, and a
digest-pinned Docker image for native **3.14.2**. The host Python **3.14.7** is
deliberately not the parity baseline. Both sides assert version and implementation.

Verified against the release's official documentation and live lockfile:

- [Module-worker requirement and example](https://pyodide.org/en/314.0.7/usage/webworker.html)
  (classic `importScripts()` workers are not supported in this release).
- [JavaScript API](https://pyodide.org/en/314.0.7/usage/api/js-api.html):
  `loadPyodide`, `indexURL`, `version`, `runPython`, `globals.set/delete`.
- [Pinned distribution lockfile](https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide-lock.json):
  `info.python=3.14.2`, `abi_version=2026_0`, `platform=emscripten_5_0_3`.
- [Playwright browser launch](https://playwright.dev/docs/api/class-browsertype#browser-type-launch).
- Recovery unit rechecked the pinned worker docs above and
  [Worker.terminate](https://developer.mozilla.org/en-US/docs/Web/API/Worker/terminate):
  termination does not wait for worker work to finish or run worker cleanup.

Runtime updates are explicit: change pins, verify official release docs/lockfile,
rerun native/WASM comparison, inspect legacy differences, then replace evidence.
No floating `stable` or latest runtime URL. Assets are fetched over HTTPS from
the versioned CDN; this is not an offline or vendored/integrity-audited bundle.

## Reproduce

Use Docker, Node **26.13.0** (`.node-version`), npm, and Playwright's matched
Chromium. All npm dependencies are isolated here, with a committed lockfile;
do not run the root legacy `npm install` or change the running legacy services.

```sh
cd prototype/pyodide
npm ci
npx playwright install chromium
npm test
docker pull python:3.14.2-slim-bookworm@sha256:e87711ef5c86aaeaa7031718a69db79d334d94c545c709583f651b8185870941
docker run --rm --network=none --read-only \
  --mount "type=bind,src=$(git rev-parse --show-toplevel),dst=/work,readonly" \
  python:3.14.2-slim-bookworm@sha256:e87711ef5c86aaeaa7031718a69db79d334d94c545c709583f651b8185870941 \
  python -B -m unittest discover -s /work/prototype/pyodide -p test_evaluator.py -v
npm run parity
npm run recovery
```

On a Playwright-supported Linux installation, ensure the documented browser
system dependencies are available. This evidence was obtained on the current
Linux host using Playwright's Ubuntu 24.04 fallback browser download; Playwright
warned that the host OS is not officially supported. Do not interpret that as
supported deployment-platform validation. No obsolete host tooling was installed.

`npm run parity` starts a short-lived loopback-only server on an ephemeral port,
runs the native baseline in a read-only/network-disabled container, launches
headless Chromium, and tears down its browser/worker/server. Ports **5000/8082**
are untouched. CDN access is needed for the browser runtime; pre-pull the Docker
image (the native subprocess has a 30 s watchdog). Nonzero exit means a version,
coverage, infrastructure, parity, Unicode display, or legacy-expectation failure.

## Contract and separation from the legacy app

- Consume only the existing **27 `engine_cases`** in
  `tests/fixtures/regex_baseline.json`; no duplicated fixture corpus.
- `evaluator.py` is the same pure Python evaluator/JSON serializer on both sides.
  It compiles patterns and evaluates match/search/findall. Symbolic flags combine
  with OR; normalized match fields preserve nulls, arrays, groups, spans and regs.
- Compare structured results and error **categories**, not exception wording.
  Unexpected Python/worker/CDN errors fail the harness, not regex-category parity.
- `native.py` refuses the wrong CPython version. The runner checks fixture and
  evaluator hashes, complete ordered case IDs, exact runtime versions, and results.
- The worker accepts only init/evaluate fixture messages, never arbitrary Python
  source. JSON case data enters Python via a string global, not code interpolation.
- A separate `legacyEngineDifferences` list compares native 3.14.2 output with
  the 3.7.7 engine expectations; it is not conflated with native/WASM parity.
- Existing **adapter** quirks remain separate and unchanged: empty findall
  becomes null, and LOCALE rejection becomes HTTP 500 in the legacy app
  ([#47](https://github.com/rscarvalho/pyregex/issues/47)). This harness intentionally
  preserves Python's `[]` and categorized `invalid_flags`, not those defects.
- Python offsets stay code points. The browser demonstrates extracting and
  displaying `é😀é` from the Unicode fixture via code-point slicing, without HTML
  interpolation or normalization. This is not yet production highlighter wiring.

## First-unit evidence

`evidence/first-parity.json` is the actual compact successful runner output on
base commit **d979858** plus this uncommitted prototype: **27/27 native/WASM agree**,
**0 differences** from the 3.7 engine expectations in this bounded corpus.
Both Python unit tests (27 subcases plus serializer/validation checks) and both
Node unit tests pass. No whole-language equivalence is implied, and version-
specific errors/new syntax outside the corpus have not been characterized.

Independent review approved this bounded first unit and independently reproduced
the 27/27 browser/native parity result. This does not approve production
integration or complete #42.

## Next bounded unit: deadline, cancel and recreation

`controller.mjs` owns the deadline on the main thread. After readiness, each
evaluation batch has **2,000 ms total**, including worker message delivery,
compilation, matching and serialization. There is no compile acknowledgement
that can postpone the timer. A result observed at/after the deadline loses even
if the timer callback has not run. Startup has its own **30,000 ms** bound.
Browser timer scheduling is not a real-time guarantee, particularly in background
tabs or under a blocked main thread; measured foreground acknowledgement is below.

Only **one pending operation** (startup OR evaluation) is allowed. Calls while
starting/busy reject immediately; there is no queue. Timeout or explicit user
cancel invalidates pending work, terminates the worker, and starts a fresh module
worker. Call `start()` to await that replacement before sending the next request.
Startup failure does not auto-retry forever; Start/retry is explicit. Worker
errors/decoding failures terminate the worker and reject the operation. Close
rejects outstanding work and prohibits resurrection. Generation, worker identity,
and monotonic request IDs filter stale messages, errors and already-queued timers.

Prototype data limits (`limits.mjs`, checked on both sides):

- 1–32 fixture-style cases/batch, match/search/findall only, six symbolic flags.
- Pattern ≤1,024, input ≤8,192, ID ≤128; aggregate ID/pattern/input ≤32,768
  JavaScript UTF-16 code units. Fixture expectations are stripped before messaging.
- Tiny UI JSON ≤65,536 code units before parsing. No Python/source execution API.
- Serialized worker output ≤1,048,576 ASCII JSON characters before posting.
  **This check occurs after Python result allocation**, so it is not a hard
  memory bound. Input caps/deadlines do not establish a safe general-purpose sandbox.
- Diagnostic UI retains the latest 32 events and 10,000 heartbeat timestamps.

`npm run recovery` repeats native/WASM parity, then uses **actual Playwright
clicks** on Evaluate/Cancel with `(a+)+$` against 128 `a`s followed by `!`.
It runs three timeout and three cancel cycles, verifies fresh generations and a
successful `a+` search after **every** recreation. Each acknowledgement and
20 ms timer/DOM heartbeat gap must be ≤250 ms; restart readiness is recorded
separately, not included in a misleading 250 ms restart claim. Unexpected page
errors fail the runner; there is no CSP change or error-event suppression.

`controller.test.mjs` deterministically tests deadline/result ordering, cancel,
close, startup bounds, busy rejection, wrong IDs/generations, stale errors and
timers across three recreations. Its silent fake worker represents either
**compile or match**. No reliable deterministic real compile hang is claimed:
this is controller instrumentation evidence only. Actual pathological matching
is exercised in Chromium, not an injected infinite Python loop.

`evidence/worker-recovery.json` records measured run data and limitations. This
slice is **unreviewed until the parent session's independent reviewer approves**.
Remaining gates: device/network/cache-defined desktop and real mobile startup,
ordinary-workload percentiles, transfer and memory, production CSP/integration,
runtime policy and explicit go/no-go. No full-runtime/performance verdict or
completion of #42 is implied.
