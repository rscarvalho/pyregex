# Issue #42: first bounded engine-parity unit

Standalone experiment for [#42](https://github.com/rscarvalho/pyregex/issues/42),
under the [#41](https://github.com/rscarvalho/pyregex/issues/41) runtime gate.
**Not production integration and not completion of #42.** No application imports,
Flask requests, legacy asset tooling, or JavaScript replacement regex engine.

## Scope and timebox

The agreed overall prototype timebox is **five engineer-days total**, including
the **half-day legacy setup (already done)**. This first unit establishes a
repeatable same-version engine comparison only; it does not extend that timebox.
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
measurement. A 60 s harness watchdog is not the required 2 s evaluation deadline.

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

## Evidence and next gate

`evidence/first-parity.json` is the actual compact successful runner output on
base commit **d979858** plus this uncommitted prototype: **27/27 native/WASM agree**,
**0 differences** from the 3.7 engine expectations in this bounded corpus.
Both Python unit tests (27 subcases plus serializer/validation checks) and both
Node unit tests pass. No whole-language equivalence is implied, and version-
specific errors/new syntax outside the corpus have not been characterized.

Next bounded unit: main-thread-owned per-request deadlines, termination of a
pathological regex, worker recreation, stale-result protection, UI heartbeat and
successful subsequent requests. Follow with actual desktop/mobile performance,
transfer and memory evidence. Only then record go/no-go and production runtime
policy. Do not feed hostile or unbounded inputs to this first-unit worker API.

Independent review approved this bounded first unit and independently reproduced
the 27/27 browser/native parity result. This does not approve production
integration or complete #42.
