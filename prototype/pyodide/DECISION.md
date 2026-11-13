# Issue #42: provisional runtime decision

**Recommendation: NO-GO now under the agreed gates; not production adoption.**
This closes the bounded evidence-gathering exercise, not every acceptance box or
the open mobile/memory gates. Independent review of the accumulated uncommitted
slice is required before commit/PR update. Nothing has been committed or pushed.

## Decision rule and scope

A GO requires the original targets and compatibility/recovery requirements to
be supported on the intended desktop **and actual mobile** environments, with
no known startup miss hidden by a different readiness definition. An unknown
gate alone would yield INCONCLUSIVE; here repeated measured desktop warm misses
already supply affirmative failure evidence. Therefore **NO-GO for adopting this
prototype as the production runtime under the current gates**, with several
other gates independently inconclusive. This is not a claim that Pyodide is
intrinsically unsuitable or that an agreed future UX/runtime redesign cannot work.
No budget, readiness boundary, fixture contract, or timebox was changed.

The overall allowance remains five engineer-days including the completed
half-day legacy setup. Startup tuning stops. This final slice is capped at two
cold/warm pairs per network profile and two memory calls, with a 240 s runner
watchdog. It does not authorize spending another timebox to obtain a pass.

## Existing evidence retained, not replaced

| Gate | Evidence and bounded interpretation |
| --- | --- |
| Same-version semantics | Pyodide 314.0.7 / CPython 3.14.2; 27/27 native/WASM fixture cases agree; zero observed legacy engine differences in that corpus only. Adapter quirks remain separately recorded. |
| Python/JS offsets | Astral and combining-character fixture displayed using code-point slicing, without normalization. Production highlighter integration remains untested. |
| Desktop cold ≤5 s | Initial n=5: 2.702–4.415 s; independent n=5: 2.716–5.527 s. Variable, **not a reliable pass**. |
| Desktop warm ≤2 s | Initial n=5: 2.121–2.196 s; reviewer n=5: 2.080–5.460 s; startup diagnosis also misses with cached CDN and loopback runtime. **Fail**; cache verified, successful probe included. |
| Desktop ordinary p95 ≤100 ms | Six workload/mode combinations, n=100 each: 0.9–1.3 ms; reviewer 0.7–1.2 ms. Pass for those explicit ordinary requests, not every regex. |
| Compressed runtime ≤15 MiB | 6,237,877 encoded-body bytes (5.95 MiB), five version-pinned resources; reproduced. Pass for pinned runtime only, not total wire/application size. |
| Deadline/recovery | 2 s main-thread evaluation deadline; three pathological timeout and three cancel/recreate cycles with successful next requests; ≤250 ms foreground acknowledgement/heartbeat checks passed. Worker restart time separately recorded, not claimed ≤250 ms. |
| Overflow | Actual bounded output overflow discards worker; explicit retry and normal request succeed. Output check occurs **after allocation**, not a peak-memory cap. |
| Mobile | No physical device available. All actual-mobile startup/evaluation/memory/recovery gates remain **inconclusive**; desktop emulation cannot satisfy them. |
| Deployment | No production CSP, CDN integrity/availability, isolation migration, supported-browser matrix, or app integration approval. |

Raw artifacts: `evidence/desktop-performance.json`,
`evidence/reviewer-desktop-performance.json`,
`evidence/performance-regression-recovery.json`,
`evidence/reviewer-performance-recovery.json`, `evidence/startup-diagnostic.json`,
and `evidence/startup-regression-recovery.json`. See [README.md](README.md) and
[STARTUP.md](STARTUP.md) for exact definitions, earlier commands and limitations.

## Final diagnostic design and reproduction

From the repository root, use the README's pinned npm/Playwright/Docker setup:

```sh
cd prototype/pyodide
npm test
node final-gates.mjs > evidence/final-gates.json
node memory-cdp.mjs > evidence/memory-cdp.json
node --test final-gates.test.mjs
```

`final-gates.test.mjs` checks the durable artifact against SHA256 of every
listed current source, versions, sample counts, original targets, and summary
distributions. These hashes establish provenance, not publisher authenticity.
Raw numerical observations and failures are retained; only ephemeral loopback
ports in URLs are replaced by `PORT`. No cookies, tokens, request headers,
machine username or absolute host paths are recorded by the new runner.

Memory and network are **separate experiments**. Only the memory server responses
add `Cross-Origin-Opener-Policy: same-origin` and
`Cross-Origin-Embedder-Policy: require-corp`; actual secure-context/isolation/API
availability is recorded. No CSP is removed, relaxed or suppressed. All local
responses remain no-store, with an exact file allowlist and ephemeral loopback
port; services on 5000/8082 remain untouched. No large runtime files enter Git.

### Documentation checked 2026-11-13

- [MDN memory API](https://developer.mozilla.org/en-US/docs/Web/API/Performance/measureUserAgentSpecificMemory):
  secure context and cross-origin isolation required; experimental,
  implementation-specific estimate of the app including frames/workers.
- [Chrome memory guidance](https://web.dev/articles/monitor-total-page-memory-usage):
  collection may await GC (documented timeout currently 20 s); some regions can
  be excluded; individual snapshots are weak evidence, not peak RSS. This runner
  does not use the documented eager-measurement flag or force garbage collection.
- [MDN COEP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Embedder-Policy):
  `require-corp` permits CORS-authorized cross-origin fetches; no-cors resources
  instead need compatible CORP. Runtime CDN response ACAO/CORP headers are retained
  from actual browser responses alongside successful isolated startup. This is
  observed compatibility of these exact URLs, **not** a general CDN guarantee.
- [Official jsDelivr documentation](https://github.com/jsdelivr/jsdelivr/blob/master/README.md):
  custom endpoints exist; its general caching text expressly excludes custom
  endpoints. It supplies no isolation-header promise for this Pyodide endpoint;
  the runner does not invent one or assume a missing CORP header is an error when
  CORS authorizes the request.
- [Playwright CDPSession](https://playwright.dev/docs/api/class-cdpsession):
  documented `newCDPSession`, `send`, events, timeout options.
- [Official CDP protocol schema](https://github.com/ChromeDevTools/devtools-protocol/blob/master/json/browser_protocol.json):
  `Network.emulateNetworkConditionsByRule` (experimental) uses bytes/s throughput,
  minimum request-to-headers latency in ms and empty-pattern global matching;
  `Emulation.setCPUThrottlingRate` uses slowdown factors. Related workers are
  explicitly paused/configured using `Target.setAutoAttach`, then resumed via
  `Runtime.runIfWaitingForDebugger`. Documented non-flat
  `Target.sendMessageToTarget` is deprecated but used only diagnostically;
  worker method rejection is recorded, never treated as inherited support.

### Exact controlled profiles

| Profile | Network cap down/up | Minimum latency | CPU request | Viewport |
| --- | --- | --- | --- | --- |
| Desktop | 2,500,000 / 625,000 bytes/s (20/5 decimal Mbit/s) | 40 ms | 1× | 1280×720 |
| Mobile-emulated | 500,000 / 125,000 bytes/s (4/1 decimal Mbit/s) | 100 ms | 4× | 390×844, touch/mobile layout |

Two independent fresh-browser pairs each; warm is a new document/worker in the
same primed context after closing the cold page. No interception disables cache.
Worker Resource Timing verifies cache state. Readiness remains navigation time
origin through the **same successful `a+` probe**. Original desktop 5/2 s and
mobile 10/4 s budgets are printed alongside observations, not shifted to allow
instrumentation. With n=2, p95=max; no outliers/warm-ups removed. CDP pauses and
commands add overhead, not a claimed exact production simulation. Throughput
caps are applied per target, not a physical shared aggregate bottleneck; the
actual uplink/CDN may be slower. CPU worker support must be read from evidence,
not inferred from successful page configuration. No emulated ordinary-workload
p95, recovery or mobile battery/thermal/ARM claim is made.

## Final observations

Durable raw data: `evidence/final-gates.json` and `evidence/memory-cdp.json`.
All eight network startups completed with the pinned versions and successful
probe, verified cold transfer/warm cache, and no page errors.

| Navigation → successful probe | Cold n=2 | Warm n=2 | Unchanged budgets |
| --- | --- | --- | --- |
| Controlled desktop | 4.315–4.363 s | 1.798–1.811 s | 5/2 s: passes **this sample** |
| Mobile layout/network, page CPU 4× | 15.022–15.073 s | 2.305–2.352 s | 10/4 s: cold misses, warm passes **this partial emulation only** |

The desktop warm passes are retained, not omitted to strengthen NO-GO. They do
not erase the repeated misses in earlier independent runs: the gate lacks
reproducible margin across runs/conditions, not an intrinsic proven >2 s floor.
Likewise the emulated warm pass cannot approve mobile. Network rules were accepted
on page and worker in every sample. The worker CPU command was rejected in all
eight samples with the observed message `Operation is only supported for pages,
not workers`; that wording is an observation, not a parsed/API-stable contract.
Thus the requested 4× slowdown is **page-only**, not verified on the runtime
worker. These are controlled-network plus layout/page-CPU observations, **not a
completed mobile CPU/network gate or a real-device result**.

### Memory result: inconclusive, not a 256 MiB pass

The isolated document reports `isSecureContext=true`, `crossOriginIsolated=true`,
and the API function present. Both calls (after ready and after 100 checked
ordinary probes) immediately reject with observed `SecurityError` / API not
available (0.715 ms and 0.050 ms). The 12 s per-call watchdog never fires. That
watchdog is intentionally shorter than Chrome's documented possible 20 s GC
delay: a watchdog expiry would be recorded as inconclusive, not unsupported or
zero usage. Here actual rejection, not slow GC, is the observed outcome. The
reason for rejection beyond the recorded browser response is **not established**;
no undocumented browser flag, CSP relaxation or bypass was tried.

All five CDN runtime responses in the isolated run report ACAO `*` and CORP
`cross-origin`, status 200, and the first probe succeeds. This verifies this
experiment's cross-origin resource compatibility with the documented policy;
it neither diagnoses the API rejection nor approves production isolation.

One separate 45 s-watchdog fallback run uses the officially documented
[CDP `Runtime.getHeapUsage`](https://github.com/ChromeDevTools/devtools-protocol/blob/master/json/js_protocol.json)
on the **page isolate only** after successful startup. It reports JS heap
`usedSize=1,452,152` and `totalSize=2,428,928` bytes, with separate
`embedderHeapUsedSize=1,383,392` and `backingStorageSize=6,530`. The schema defines
isolate-level heap/backing-storage fields; it does not define a sum as total app
memory. The live Pyodide worker is **not included**. These numbers are partial
diagnostic data, not a substitute for the failed whole-app API, a 256 MiB pass,
process RSS, worker WASM memory, or peak allocation. No total/peak memory verdict
is available, and actual-mobile memory remains unmeasured.

### Validation and accumulated scope

`npm test`: **9/9**; pinned native Python tests: **3/3**, including all 27 fixture
subcases. `node --test final-gates.test.mjs`: **3/3**, including current-source
hash validation of both new artifacts. Existing 27-case parity / six-cycle
recovery / overflow evidence was retained rather than rerun because no runtime,
controller, evaluator or recovery implementation changed in this final slice.

All accumulated writes remain in `prototype/pyodide/`: the pre-existing reviewed
performance and startup harnesses/docs/raw evidence plus this decision, two
diagnostic runners, evidence tests and two raw artifacts. Tracked inherited
changes are README/package scripts, recovery's overflow check and its native
test; these were preserved, not attributed to this final slice. No backend,
legacy application, production header/CSP, dependency pin or service changes.

## Conditional runtime policy and next action

**Only if a future user-approved decision selects Pyodide:** retain exact release
and bundled CPython pins; require version/lockfile checks, same-version native
parity and explicit legacy-difference review, Unicode display tests, worker
timeout/cancel/overflow recreation, startup/transfer/memory/device evidence and
security/deployment review before each runtime update. No floating CDN stable or
latest URL. Revisit the corpus for newly supported syntax/errors; never silently
switch to JavaScript regex semantics. These are conditional requirements, **not
an assertion of production adoption or implemented release automation**.

Parent next action: obtain independent review of **all accumulated uncommitted
performance, startup and final-gate sources/artifacts**, then present this NO-GO
recommendation and unresolved gates for user decision. Delegation tools were not
available in this subagent; no independent review of this slice is claimed.
Backend remediation [#49](https://github.com/rscarvalho/pyregex/issues/49) is a
conditional follow-up if authorized; **do not start it, change production, commit,
push, or silently broaden runtime work without the parent/user's approval**.
