# Issue #42: bounded parity, worker recovery and desktop measurements

Standalone experiment for [#42](https://github.com/rscarvalho/pyregex/issues/42),
under the [#41](https://github.com/rscarvalho/pyregex/issues/41) runtime gate.
**Not production integration and not completion of #42.** No application imports,
Flask requests, legacy asset tooling, or JavaScript replacement regex engine.

## Scope and timebox

The agreed overall prototype timebox is **five engineer-days total**, including
the **half-day legacy setup (already done)**. The first unit established engine
parity; the next adds bounded worker recovery. Neither extends that timebox.
The following bounded slice adds desktop measurements, not production optimization.
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

These are **targets, not a general performance verdict**; the bounded desktop
observations below define device, network/cache conditions, ordinary workload,
sample count, readiness boundaries and memory availability. No actual mobile
evidence exists. The native container's 256 MiB safety limit is not a browser-memory
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
node performance.mjs > evidence/desktop-performance.json
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

`evidence/worker-recovery.json` records the earlier measured run. The subsequent
`evidence/performance-regression-recovery.json` reruns 27/27 native/WASM parity
and all six cancel/timeout cycles, then exercises **output overflow** using one
bounded findall request: 8,192 ASCII characters and 32 tiny captures in a lookahead.
The native test confirms 8,193 results and serialized output between 1 MiB and
1.5 MB. The real browser rejects it as infrastructure failure, discards the worker,
and succeeds on a normal request after explicit retry. This is not a peak-memory
test or a pre-allocation cap. A deterministic real compile hang remains untested;
no risky resource-amplifying compile experiment was needed for this slice.

## Bounded desktop performance evidence (independently reviewed)

`performance.mjs` and `performance-page.mjs` use the unchanged controller and
worker, an isolated loopback server on an ephemeral port, and actual headless
Chromium. `npm run performance` prints JSON (redirect `node performance.mjs`
directly to avoid npm's banner in the evidence). It does not tune the runtime or
change production assets, headers, CSP, or the existing services.
Budget misses are recorded as JSON statuses, not an exit-code failure; nonzero
exit indicates an infrastructure, version, or workload-correctness failure.

Fresh documentation checked for this slice:

- [W3C Resource Timing, 2026-11-02 draft](https://www.w3.org/TR/2026/CRD-resource-timing-20261102/):
  worker-local resource timelines, `encodedBodySize`, `decodedBodySize`,
  `transferSize`, local-cache zero transfer, cross-origin/TAO restrictions.
- [Playwright Browser.newContext](https://playwright.dev/docs/api/class-browser#browser-new-context):
  contexts do not share cookies/cache; [Worker.evaluate](https://playwright.dev/docs/api/class-worker#worker-evaluate)
  reads the actual worker's resource timeline, not the page-only timeline.
- [Pinned Pyodide API](https://pyodide.org/en/314.0.7/usage/api/js-api.html):
  module loader, `pyodide.asm.mjs`, lockfile and stdlib URLs. Required startup
  resources are checked against the observed version-pinned browser fetches.
- [Python re](https://docs.python.org/3.14/library/re.html): recent compiled
  patterns are cached; `(?#...)` comments do not change matching semantics.
- [Memory API](https://developer.mozilla.org/en-US/docs/Web/API/Performance/measureUserAgentSpecificMemory):
  secure-context/cross-origin-isolation requirements, implementation-dependent
  web-app estimates including workers, not process RSS or a portable peak bound.

### Definitions and conditions

- **Cold:** five independent fresh Chromium processes/contexts, empty browser
  HTTP cache. OS, DNS, TLS and upstream/CDN caches are **not** guaranteed cold.
- **Warm:** new document and new worker in the same primed context; previous
  page closed. All five runtime resources report positive body sizes and
  `transferSize=0` in every warm sample. This is **not** reuse of a live interpreter.
  Local harness assets remain `Cache-Control: no-store` in both phases.
- **Whole startup:** navigation time origin through page/module loading, worker
  creation, runtime initialization, version checks, evaluator installation, and
  the response to a successful `a+` search. Browser launch is excluded; no claim
  about production UI paint. Controller-only startup and probe time are separate.
- **Evaluation:** 100 serial end-to-end controller requests for each of three
  explicit ordinary workloads (log search, Unicode match, token findall), for
  **600 samples total** on the final live warm worker. Each workload runs both
  repeated-pattern (includes first compile) and unique-comment-pattern modes.
  The latter avoids reuse of identical compiled patterns, but does not isolate
  compiler time. All outputs are checked, no outliers or warm-ups discarded.
- Distributions retain raw samples, min, nearest-rank median/p95 and max. With
  only five startup samples, p95 equals max; this is not an SLA estimate.
- **Network:** live pinned jsDelivr HTTPS, no network/CPU throttling, no request
  interception, no mobile emulation. Local page is loopback. Actual host uplink,
  bandwidth, DNS, proxies and CDN conditions are uncharacterized, **not controlled**.
- **Device/browser:** Intel Core i7-11800H @ 2.30 GHz, 16 logical CPUs, x86_64
  Linux `7.2.15-1-omarchy`, Chromium **158.0.8127.18**, Playwright **1.65.0**,
  Node **26.13.0**, headless 1280×720. Full OS release/host RAM/user agent and
  source hashes are in the JSON. Shared-host load/power are not controlled;
  Playwright's unsupported-host/fallback-build limitation still applies.

### Observations, not a general performance approval

`evidence/desktop-performance.json`, base **9a9854a** plus hash-identified
uncommitted measurement sources:

| Desktop metric | Observation | Target | Bounded result |
| --- | --- | --- | --- |
| Cold navigation → usable, n=5 | 2.702–4.415 s; median 2.766 s | ≤5 s | Pass in this sample |
| Primed-cache navigation → usable, n=5 | 2.121–2.196 s; median 2.154 s | ≤2 s | **Fail** (all five over target) |
| Ordinary evaluation, n=100 per workload/mode | p95 0.9–1.3 ms | ≤100 ms | Pass for these workloads only |
| Runtime encoded response bodies | 6,237,877 bytes = 5.95 MiB, identical in five cold samples | ≤15 MiB | Pass for this pinned runtime |
| Total/peak memory | API unavailable; not cross-origin isolated | ≤256 MiB | **Inconclusive** |

Independent review reproduced parity, recovery and the test suites, and ran a
second performance sample: cold startup **2.716–5.527 s**, cached startup
**2.080–5.460 s** (cache confirmed), ordinary evaluation p95 **0.7–1.2 ms**,
and identical runtime transfer totals. Both startup targets failed in that run.
Thus the first sample's cold pass is not a reliable general cold-start verdict;
the original budgets remain unchanged. Reviewer raw artifacts are now retained
durably in `evidence/reviewer-desktop-performance.json` and
`evidence/reviewer-performance-recovery.json` (copies of the host's original JSON).

Transfer sums **`encodedBodySize`**, not decoded WASM/ZIP sizes. The five
observed runtime files are `pyodide.mjs`, `pyodide.asm.mjs`, `pyodide.asm.wasm`,
`python_stdlib.zip`, and `pyodide-lock.json`. Per-resource compressed/decoded
sizes and browser-reported `transferSize` are preserved. This excludes local
application assets and is not literal packet/TLS/header traffic. Zero/missing
body sizes make the verdict inconclusive, not a false zero-byte pass.

`measureUserAgentSpecificMemory` is unavailable in this non-isolated harness.
No flags/headers were changed to force availability. Neither JS heap, WASM
linear-buffer capacity, native container limits nor host RAM stand in for total
browser memory. A usable API would still yield an implementation-specific
snapshot estimate, not an allocation limit or peak guarantee.

**No mobile hardware was available; all actual-mobile budgets remain open.**
No desktop emulation is presented as mobile evidence. Independent review is
required before committing this slice; no runtime go/no-go follows from these
numbers. Remaining gates include the warm-start miss, actual mobile devices,
representative/controlled networks, memory where measurable, production
CSP/integration and runtime policy within the existing five-day total timebox.

## Bounded startup diagnosis (awaiting independent review)

See [STARTUP.md](STARTUP.md) and `evidence/startup-diagnostic.json` for the
CDN-versus-loopback experiment, documented pre-interpreter boundary, raw resource
timings, CPU/load observations, and limitations. Cached navigation still exceeds
2 s in both conditions; page/module and probe overhead are small. This does **not**
prove Python initialization itself has an unavoidable >2 s floor. No production
configuration, controller, worker source, readiness criterion, or budget changed.

## Final bounded gates and provisional decision (awaiting independent review)

See [DECISION.md](DECISION.md) for exact commands/profiles, sanitized raw evidence,
source-hash validation and the **NO-GO now under the unchanged gates** recommendation.
The new controlled-desktop n=2 sample passes 5/2 s (including cached starts below
2 s); earlier repeated warm misses and cold variance are not erased. The
mobile-layout/network sample misses 10 s cold startup; worker CPU emulation was
unsupported, and no real mobile evidence exists. Isolated memory calls reject;
page-only CDP heap data does not close the 256 MiB total/peak-memory gate.
All current production settings and runtime sources remain unchanged. Independent
review and parent/user decision are required; backend #49 is conditional, not started.
