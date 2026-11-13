# 0001: Retain server-side Python regex evaluation

## Status and date

Accepted — 2026-11-13.

## Context

PyRegex tests Python regular expressions, so its results should reflect CPython's
`re` behavior. The current app evaluates expressions on a Python backend. The
Pyodide experiment explored running CPython in a browser worker instead. That is
still Python regex evaluation, not a switch to JavaScript's regex engine.

The experiment had a five-engineer-day limit and agreed gates for compatibility,
startup, execution, transfer size, memory, and recovery on desktop and actual
mobile devices. It produced useful evidence, but did not establish a production
replacement that meets those gates.

## What we decided

Keep server-side Python regex evaluation for now. Do not adopt the Pyodide
prototype as the application's runtime. This accepts the experiment's provisional
**NO-GO now under the unchanged gates**, not a permanent rejection of Pyodide.

This is a runtime direction, not permission to change production infrastructure
or implement backend remediation in [#49](https://github.com/rscarvalho/pyregex/issues/49).
It also does not certify the existing backend as safe.

## Why

Compatibility and execution were encouraging: all 27 same-version native/WASM
fixtures agreed, ordinary requests were fast, and the tested timeout,
cancel/recreate, and overflow recovery checks passed. Those results cover the
tested cases, not every regex or production integration.

Startup was not consistently within budget. Some desktop warm samples met the
two-second target; repeated independent samples missed it. Cold desktop results
also varied. This is evidence of insufficient reliable margin, not proof of an
unavoidable startup floor. The startup diagnosis did not establish a measured
fix that reliably meets the target.

Partial mobile emulation took about 15 seconds cold against a ten-second target.
The worker's requested CPU slowdown was not applied, so this was not a completed
mobile gate or an actual-device failure. Actual-mobile results remain unknown.
Total and peak memory are also inconclusive; the available page-only heap sample
does not measure the live Pyodide worker or establish a memory-budget pass.

The pinned runtime met the transfer-size budget, but that and fast execution do
not resolve the startup misses or the open mobile, memory, and deployment checks.

## What next

Stop runtime adoption work at this decision. Keep the experiment and its evidence
linked below; there is no need to merge prototype code into the application.
The user plans to close draft PR #56 separately. Closing it leaves the PR
discussion available and commit links generally accessible, but is not an
archival guarantee.

Any backend remediation, including #49, needs separate approval and its own
scope and review. This record does not implement that work, authorize production
changes, or close any issue.

## Revisit

Revisit if new evidence supports the unchanged gates, or if the user explicitly
approves different requirements or a different startup experience. A new proposal
should address reproducible startup margin, actual-device mobile checks, total
and peak memory, app integration, and security/deployment review. Keep the
compatibility and recovery checks, with explicit runtime versions; do not quietly
substitute JavaScript regex semantics.

Record a replacement decision here if that changes the chosen direction.

## References

The experiment links below use commit
`f7360bd22cd4efaf7815e3ba10eb285eaf46f9b5`, not its moving branch. The experiment
documents include historical workflow notes; this record captures the accepted
runtime decision.

- [Final recommendation and gate evidence](https://github.com/rscarvalho/pyregex/blob/f7360bd22cd4efaf7815e3ba10eb285eaf46f9b5/prototype/pyodide/DECISION.md)
- [Startup diagnosis and limitations](https://github.com/rscarvalho/pyregex/blob/f7360bd22cd4efaf7815e3ba10eb285eaf46f9b5/prototype/pyodide/STARTUP.md)
- [Experiment setup, compatibility, and recovery](https://github.com/rscarvalho/pyregex/blob/f7360bd22cd4efaf7815e3ba10eb285eaf46f9b5/prototype/pyodide/README.md)
- [Final startup observations](https://github.com/rscarvalho/pyregex/blob/f7360bd22cd4efaf7815e3ba10eb285eaf46f9b5/prototype/pyodide/evidence/final-gates.json)
- [Memory observations](https://github.com/rscarvalho/pyregex/blob/f7360bd22cd4efaf7815e3ba10eb285eaf46f9b5/prototype/pyodide/evidence/memory-cdp.json)
- [Runtime investigation #42](https://github.com/rscarvalho/pyregex/issues/42)
- [Draft experiment PR #56](https://github.com/rscarvalho/pyregex/pull/56)
- [Backend remediation #49 — separate approval required](https://github.com/rscarvalho/pyregex/issues/49)
