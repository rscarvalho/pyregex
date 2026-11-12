# Isolated local baseline — issues #42 / #41

This is an isolated legacy baseline, not a production deployment or a Pyodide
implementation. Python 3.7, Debian Buster and the locked packages are obsolete;
keep this service local and use synthetic inputs only.

## Run

Requires Docker Engine and Docker Compose. No host Python, Pipenv, Node or global
legacy tooling is needed. From the repository root:

```sh
docker version
docker network ls
docker compose -f compose.local.yaml build backend
docker compose -f compose.local.yaml up -d --no-deps backend
docker compose -f compose.local.yaml ps
```

The API is at `http://127.0.0.1:5000/api/regex/test/` (there is no index route).
Port 5000 must be free. The explicit `PORT=5000` satisfies `uwsgi.ini`.
Publishing is restricted to host IPv4 loopback; do not change it to a public bind.
The process listens on container interfaces so Docker forwarding works.

The image pins Python **3.7.7** and its image digest, matching `.python-version`
and the Pipfile's 3.7 target. `runtime.txt` historically says 3.7.6; it is untouched.
`locked_requirements.py` exports both sections of the existing `Pipfile.lock`
with hashes; pip verifies downloaded artifacts without re-locking. Build tools
(pip/setuptools/compiler) come from the pinned base image. No dependency upgrades
or host mounts are involved. Rebuild after source changes.

The container runs as an unprivileged numeric user with a read-only filesystem,
temporary `/tmp`, dropped capabilities and CPU/memory/process limits. No tokens
or host environment secrets are passed. Build requires Docker Hub and PyPI
network access. Runtime does not require external services, but outbound network
access is not disabled: this is not a sandbox for hostile inputs.

## Verify with deadlines

```sh
docker compose -f compose.local.yaml exec -T backend timeout -k 5s 60s nosetests -c nose.cfg
docker compose -f compose.local.yaml exec -T backend timeout -k 2s 30s python local/smoke.py
curl --max-time 6 --fail --get \
  --data-urlencode 'regex=\w+' \
  --data-urlencode 'test_string=Hello, World!' \
  http://127.0.0.1:5000/api/regex/test/
```

The smoke script verifies findall, no-match, invalid-regex (400), and pathological
backtracking (422), with a six-second HTTP timeout per request. Existing tests
cover match/search, flags, groups and timeouts. External command deadlines are
important: the existing multiprocessing/queue code can hang in failure cases.
uWSGI also has a local-only ten-second worker harakiri; this does not fix the
underlying service behavior.

Verified on Linux x86_64, 2026-11-12:

- Docker daemon/network enumeration, image pull and PyPI downloads succeeded.
- Image build succeeded using the unchanged lock and hash verification.
- All **20 tests passed in 4.442 seconds**.
- All **four HTTP smoke checks passed** against the running uWSGI service.
- Host curl returned `{"result":["Hello","World"],"result_type":"findall"}`.
- Compose reported `127.0.0.1:5000->5000/tcp` only.

Stop/remove this setup's container and network (keeps the image):

```sh
docker compose -f compose.local.yaml down
```

## Isolated frontend (bounded investigation)

Keep an already running backend untouched; these commands target only frontend:

```sh
docker compose -f compose.local.yaml build frontend
docker compose -f compose.local.yaml up -d --no-deps frontend
docker compose -f compose.local.yaml exec -T frontend node local/frontend-test.js
curl --fail --max-time 6 http://127.0.0.1:8082/assets/application.js -o /dev/null
```

Open `http://127.0.0.1:8082/`. The compiled bundle explicitly targets
`http://127.0.0.1:5000/api`; the browser accesses that host endpoint directly.
No backend dependency/recreation, host mounts, credentials or global host tools
are required. Stop just this frontend with:
`docker compose -f compose.local.yaml stop frontend` (do not use `down` when
keeping the backend alive).

The digest-pinned Node 18.20.8 image runs the original Grunt 0.4/CoffeeScript/LESS
development build. This is a compatibility harness, **not** a reproduction of
Node 0.10.13 and **not** a supported or secure production stack. The local-only
package manifest/lock selects build plugins without S3, watchers, desktop
notifications or the retired Karma/PhantomJS runner. `npm ci --ignore-scripts`
verifies the npm lock; Bower components use immutable Git commits and SHA-256
archive hashes in `frontend-components.json`, without needing Bower/git at build
time. Network access to npm and GitHub codeload is required for builds.

Unbounded historical Bower jQuery constraints now select incompatible jQuery 4;
the local manifest deliberately pins jQuery 1.11.3 (not an assertion of the
original deployed version). Other snapshots match resolutions within historical
constraints, retaining Angular 1.0.7. Root manifests, Gruntfile and application
sources remain unchanged. Never run `grunt deploy` or production tasks.

Only container-generated output changes: the API host becomes IPv4 loopback;
analytics, external stylesheet links and remote images are removed. The static
server adds a CSP allowing connections only to itself and the local backend,
with local scripts/styles/images. Its local-only `unsafe-eval` exception is
required by the legacy Angular expression compiler; it is not a production CSP.
External hyperlink destinations remain clickable; do not
follow them if keeping the session entirely offline. Missing external icon/font
styling is expected. Runtime outbound network is not sandboxed.

Verified on Linux x86_64, 2026-11-12:

- Image build completed the original Grunt development tasks; 14 CoffeeScript
  files passed lint and application JS/CSS/templates were generated.
- HTTP checks confirmed built assets and the loopback API configuration; API
  requests with frontend Origin returned a successful result and matching CORS.
- Supplemental `frontend-test.js` runs the 17 existing CoffeeScript specs under
  Jasmine 1.3/jsdom: 51 assertions passed. Only endpoint expectation strings are
  adapted in memory to match the local output. Modernizr emits a jsdom canvas
  not-implemented warning. This is **not** the historical Karma/PhantomJS runner
  and does not validate real browser rendering, layout, canvas or user interaction.
- A subsequent Playwright Chromium run verified match/search/findall, invalid
  regex errors, ignore-case, permalink restoration and changelog navigation
  with CSP enforced (no CSP bypass). No page errors or failed requests were
  recorded; the invalid-regex HTTP 400 was expected. Local evidence is at
  `/tmp/opencode/pyregex-playwright/evidence.json` (not committed). This is not
  exhaustive visual, accessibility or cross-browser verification.

The proposed Pyodide experiment remains future work; none is implemented here.
