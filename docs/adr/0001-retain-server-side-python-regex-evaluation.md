# 0001: Retain server-side Python regex evaluation

## Status and date

Accepted — 2026-11-13.

## Context

PyRegex tests Python regular expressions, so its results should reflect CPython's
`re` behavior. The current app evaluates expressions on a Python backend. The
Pyodide experiment explored running CPython in a browser worker instead. That is
still Python regex evaluation, not a switch to JavaScript's regex engine.

We gave the experiment five days to check compatibility, loading time, download
size, memory use, and recovery from slow expressions. The main question was
whether we could remove the backend without making the app worse to use.

## What we decided

Keep running expressions on the Python backend. We don't have enough confidence
in Pyodide's loading time and mobile performance to replace it yet.

The backend still needs the security and maintenance work listed in
[#41](https://github.com/rscarvalho/pyregex/issues/41). Keeping it doesn't mean
leaving it as it is.

## Why

The regex results looked good. All 27 test cases produced the same results in
Pyodide and native CPython at the same version. Ordinary requests were fast. We
could stop a stuck expression, restart the worker, and run another request
without freezing the page.

Loading Python was the problem. We wanted the app ready within five seconds on
desktop, or two seconds with the runtime already cached. Some runs passed and
others didn't. Serving the runtime locally helped cold loads but didn't reliably
get cached loads below two seconds. We didn't find a fix within the experiment's
time limit; that doesn't mean one is impossible.

With a slower network and a mobile-sized page, cold loading took about 15 seconds,
above our ten-second mobile target. That wasn't a real phone test, and the browser
wouldn't apply CPU throttling to the worker. We still don't know how it performs
on an actual phone.

The runtime download was 5.95 MiB, below our 15 MiB limit. We couldn't get a useful
total-memory measurement: the browser rejected the memory API calls, and its
page-only heap figures left out the Python worker.

Fast matching and a reasonable download size weren't enough to offset uncertain
loading times and the missing phone and memory measurements.

## What next

Close the experiment without merging its prototype into the app. The results are
linked below so we can use them if we try this again.

Plan the backend work separately in
[#49](https://github.com/rscarvalho/pyregex/issues/49).

## Revisit

Try again if a newer runtime or a different loading approach looks likely to meet
our targets. Before switching, we'd still need repeatable loading times, tests on
real phones, and useful memory measurements, alongside the compatibility and
recovery tests we already have.

If we decide to switch later, add another ADR explaining what changed.

## References

- [Final recommendation and gate evidence](https://github.com/rscarvalho/pyregex/blob/f7360bd22cd4efaf7815e3ba10eb285eaf46f9b5/prototype/pyodide/DECISION.md)
- [Startup diagnosis and limitations](https://github.com/rscarvalho/pyregex/blob/f7360bd22cd4efaf7815e3ba10eb285eaf46f9b5/prototype/pyodide/STARTUP.md)
- [Experiment setup, compatibility, and recovery](https://github.com/rscarvalho/pyregex/blob/f7360bd22cd4efaf7815e3ba10eb285eaf46f9b5/prototype/pyodide/README.md)
- [Final startup observations](https://github.com/rscarvalho/pyregex/blob/f7360bd22cd4efaf7815e3ba10eb285eaf46f9b5/prototype/pyodide/evidence/final-gates.json)
- [Memory observations](https://github.com/rscarvalho/pyregex/blob/f7360bd22cd4efaf7815e3ba10eb285eaf46f9b5/prototype/pyodide/evidence/memory-cdp.json)
- [Runtime investigation #42](https://github.com/rscarvalho/pyregex/issues/42)
- [Draft experiment PR #56](https://github.com/rscarvalho/pyregex/pull/56)
- [Backend modernization #49](https://github.com/rscarvalho/pyregex/issues/49)
