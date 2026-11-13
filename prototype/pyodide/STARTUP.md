# Issue #42: bounded startup diagnosis

**Diagnostic only; independent review required before committing.** Continues
draft PR #56 on base `9a9854a`, preserving the reviewed, uncommitted desktop
measurement slice. This is one bounded experiment inside the existing **five
engineer-day total**, not authorization for an open-ended optimization project.

## Question and result

Is the cached navigation miss network/harness overhead or interpreter startup?
The dominant observed span is **inside `loadPyodide`, after its documented
pre-interpreter `fsInit` hook**. Removing external runtime network transfer helps
cold startup but does not meet the unchanged **2,000 ms** warm-navigation target.
It is **not** evidence that Python initialization alone inevitably exceeds 2 s:
the API does not isolate that subphase, the dominant span is often below 2 s,
and same-document worker recreation has different measured results below.

`evidence/startup-diagnostic.json` retains all **12** measured startups: three
independent cold/warm browser-context pairs per condition, alternating condition
order. No sample or outlier is removed. Nearest-rank p95 equals max at n=3;
these are diagnostic observations, not population/SLA estimates.

| Navigation → first successful probe | Min–max | Median | Target |
| --- | --- | --- | --- |
| CDN, cold, n=3 | 2.681–3.867 s | 2.731 s | 5 s |
| CDN, verified HTTP cache, n=3 | 2.152–2.324 s | 2.173 s | **2 s: all miss** |
| Loopback runtime, cold, n=3 | 2.158–2.228 s | 2.204 s | 5 s |
| Loopback runtime, verified HTTP cache, n=3 | 2.090–2.267 s | 2.116 s | **2 s: all miss** |

Cold median improvement is approximately **527 ms**; warm median improvement
approximately **57 ms**. These differences are not causal effect estimates on a
controlled machine. The CDN cold 3.867 s sample is retained, including its longer
fetch span. Previous review also observed >5 s startups; this sample does not
erase those observations or establish a reliable cold pass.

## Observable boundaries (all 12 samples)

| Boundary | Evidence / interpretation |
| --- | --- |
| Navigation → page-module body | 10–20 ms; includes document, page-module and static controller/limits imports, parse/scheduling. Navigation and page Resource Timing retained. |
| Worker construction | Main-thread timestamps around actual `new Worker`; worker-local module entry mark plus both time origins retained. Worker module/dependency fetch, evaluation and message scheduling are not separately identifiable CPU phases. |
| Runtime pin and loader | Worker marks before initialization, after pin JSON, and after dynamic `pyodide.mjs` import. Import span includes fetch/parse/evaluation, not only download. |
| Runtime transfer/cache reads | All five runtime fetches retained with start/response/end, body and transfer sizes, protocol and cache metadata. In every sample all five resource fetches finish before `fsInit`. Cached WASM reads can still take ~0.13–0.18 s; zero transfer is not zero time. |
| `loadPyodide` call → `fsInit` | Cached samples: 204–246 ms. Includes overlapping resource reads and runtime setup; not a standalone WASM-compilation measurement. |
| `fsInit` → `loadPyodide` resolution | **1.811–2.003 s**, dominant observed span. Hook is before `main()`/interpreter start; span includes interpreter and Pyodide bootstrap/scheduling, not isolated Python initialization or guaranteed CPU execution. |
| Evaluator | Separate fetch/body-read mark, then `runPython` installation: **32–40 ms**. Version check also separately marked. |
| First successful readiness probe | **2.4–3.3 ms**, included in every navigation total, never skipped or redefined. |
| Same live interpreter, subsequent probe | Ten checked requests per startup, **120 raw samples**, 0.5–1.4 ms, no discarded warmups. Not a replacement for navigation readiness. |

Worker and page `performance.now()` values have different origins. Align using
the recorded `timeOrigin` values if needed; do not directly subtract their local
timestamps. Fetch spans overlap streaming compilation/setup and each other:
**summing fetch durations or subtracting their sum from `loadPyodide` is invalid**.
Separate WASM compilation, instantiation, exact interpreter initialization versus
Pyodide bootstrap, and browser code-cache hits remain **unobservable here**.

### Fresh official API check

Checked the pinned [314.0.7 JavaScript API](https://pyodide.org/en/314.0.7/usage/api/js-api.html)
on 2026-11-13. `loadPyodide({ indexURL, fsInit })` is documented; `fsInit` permits
filesystem modifications before `main()` and interpreter start, with empty
site-packages guaranteed. Here it only records a timestamp, touches no filesystem,
and invents no internal callbacks. There is no claimed compilation-complete hook.

The same docs define `stdLibURL` and `lockFileURL` defaults relative to `indexURL`;
no overrides are necessary. `fullStdLib` is deprecated and has no effect.
`packageCacheDir` is Node-only and ignored in browsers. The experimental
`createPyodideModule` option is expressly not intended for this use case. None
is used as an unsupported startup shortcut. No packages are preloaded.

## Reproduction and isolation

```sh
cd prototype/pyodide
node startup-diagnostic.mjs > evidence/startup-diagnostic.json
```

Use the README's pinned Node/Playwright setup. Downloads **only five explicitly
named assets** from pinned `runtime.json` into
`/tmp/opencode/pyodide-startup-assets-314.0.7`, never into Git. Manifest retains
decoded sizes, SHA256, exact URLs and local gzip sizes. SHA256 is provenance of
the downloaded copies, **not** independent publisher-integrity verification.
No browser request interception is used, so HTTP cache is not disabled.

The ephemeral loopback-only server has an exact allowlist, no directory traversal
or application service exposure, and touches neither port **5000** nor **8082**.
It serves instrumented in-memory copies of the existing worker/page, with
asserted unique source anchors and original/served source hashes in the evidence.
Only the experiment's loopback `runtime.json` response changes `indexURL`.
Both conditions receive identical timing instrumentation; production files,
controller deadlines, readiness probe, runtime pins, CSP and headers are unchanged.
The callback adds measurement overhead; exact zero-overhead equivalence is not
claimed. Local runtime copies use gzip and a cacheable response; harness files
remain no-store. Different compression/origin/transport means this is a network
removal diagnostic, **not** a hosting rollout or transfer-budget comparison.

Cold samples use fresh Chromium processes and isolated contexts, with positive
`transferSize` for **every** runtime resource. Warm samples use a new page and
worker in the same primed context, with positive body sizes and **zero transfer
for every resource**. Each previous page closes first. HTTP cache state is
verified; OS/DNS/TLS/CDN caches and browser machine-code caches are uncontrolled.

Host: i7-11800H, 16 logical CPUs, Linux 7.2.15-1-omarchy, headless Chromium
158.0.8127.18 / Playwright 1.65.0 / Node 26.13.0. Per-logical-CPU cumulative times
and load averages before/after every startup are retained; observed pre-sample
one-minute load was **0.90–1.29**. Neither load/power, frequency nor uplink is
controlled; low load average does not establish an idle or fixed-frequency CPU.
Playwright's unsupported-host Ubuntu-fallback limitation still applies.

## Regression and recommendation

No controller or on-disk worker changes. `npm test`: **9/9**; pinned native Python
tests: **3/3**, including 27 fixture subcases and output-overflow allocation check.
`evidence/startup-regression-recovery.json`: **27/27 native/WASM parity**, no legacy
differences, all three timeout and three cancel/recreate cycles successful, normal
request after each replacement, output-overflow discard/retry successful.
Same-document recreation measured **1.846–1.898 s** to controller readiness,
then **12.8–14.6 ms** to its checked normal evaluation. This is a different boundary
and cache/lifecycle condition, not a pass for the navigation budget. It is another
reason **not** to claim an unavoidable universal >2 s initialization floor.

**Recommendation:** do not spend the remaining prototype time on page-module
micro-optimization or assume local hosting will fix warm readiness. Network work
has plausible cold-start value, but cached startup is dominated by opaque runtime
bootstrap. Keeping a ready worker alive is already fast; prestarting it can overlap
latency with user work, but cannot truthfully reduce this navigation-to-probe
metric and is not implemented. Browser code-cache reuse might matter across
lifecycles, but has not been isolated or shown reliable. No documented, measured
configuration change here establishes enough margin for the warm target.

Stop this diagnostic slice here rather than widen it into runtime internals or
production integration. Independent review of sources/raw artifacts is the next
step. If the overall five-day allowance has room, choose the outstanding actual
mobile and controlled-network gates deliberately; otherwise report those open
instead of extending the timebox. **No runtime go/no-go**: actual mobile and
total/peak memory remain unmeasured. Cross-origin isolation/memory experiments
were deliberately not added; no production security policy was weakened.

Earlier reviewer raw JSON is now durable at
`evidence/reviewer-desktop-performance.json` and
`evidence/reviewer-performance-recovery.json`, rather than only host-temporary
paths. Those approvals cover the previous slice, **not** this new diagnostic.
