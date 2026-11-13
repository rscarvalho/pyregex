# Python characterization corpus

`regex_baseline.json` is UTF-8 JSON (no Python literals or executable patterns
outside JSON strings). `tests/fixture_tests.py` loads it relative to its own file;
the existing `nosetests -c nose.cfg` command discovers the tests, including in
the backend Docker image and `ci/smoke.sh`. No additional dependencies are needed.

## Two separate contracts

- `engine_cases`: **27** bounded Python `str` / `re` cases, independent of the
  application's serializer. Inputs specify an operation, pattern, input string
  and symbolic flag names. Results are JSON values; successful match/search
  objects use the documented normalized fields. Errors specify categories,
  not interpreter-version-specific messages. Empty findall results remain `[]`.
- `adapter_cases`: **28** legacy service/API cases. Most explicitly reference
  an engine expectation; overrides identify confirmed quirks. The extra invalid
  operation tests service validation / API HTTP 400, not a Python regex feature.
  Each case runs through both `RegexService` and the in-process GET API.

The engine baseline is CPython **3.7.7**, not a claim of equivalence across Python
versions or arbitrary JavaScript regex engines. A future native/WASM runner
should consume only `engine_cases` first, use the same Python version, combine
the named flags, and normalize match objects as described in `metadata`.
Code-point offsets are intentional: the Unicode case includes an astral
character before the match and precomposed/combining characters inside groups.
Do not normalize Unicode or substitute UTF-16 offsets. `|a` captures Python 3.7's
empty-then-nonempty findall behavior.

All six UI-exposed flags (I/L/M/S/U/X) are represented, including meaningful
I+M and S+X combinations. LOCALE rejection for `str` is Python semantics; exposing
it and turning that rejection into an unstructured API 500 is the legacy quirk.
No bytes/locale-dependent matching, timing benchmarks, hostile regex corpus,
exhaustive flag powerset, browser empty-input behavior or WASM implementation is
claimed here. Existing timeout tests remain separate.

## Confirmed quirks, not desired engine behavior

- **FIXME [#47](https://github.com/rscarvalho/pyregex/issues/47):**
  `dict_from_object` converts an empty findall list into `None` / JSON `null`.
  The two adapter overrides preserve that observation without contaminating
  the engine expectations. Successful zero-length matches are *not* no-match.
- **FIXME [#47](https://github.com/rscarvalho/pyregex/issues/47):** LOCALE with
  string input raises `ValueError`; the API's validation-error formatter assumes
  multiple arguments and instead raises `IndexError`. Assert HTTP 500 only,
  without freezing Flask's HTML page or either exception's wording. The Flask
  error log from this characterization case is expected.

Normal no-match `null` for match/search, unmatched optional groups, tuple-to-array
serialization and code-point offsets are intentional contracts, not FIXMEs.
These are characterization tests: a future fix should update the corresponding
adapter expectation deliberately, while leaving pure engine semantics separate.
