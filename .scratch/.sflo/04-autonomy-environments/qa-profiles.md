# Three-profile functional QA

**PASS for this functional slice**, candidate `51479e9663f810e33031774abceca067cd761a48`. Independent s-qa against the Stage 3 contract. No overall Stage 3 acceptance or target-model qualification.

| Condition | Observed result |
|---|---|
| Cold package preparation | All three CLI prepare commands succeed with new empty stores and `--project` validation, without model configuration. Existing pinned base images reused; package caches and dependency snapshots fresh. Receipts bind locks, artifacts and tree: API 16 wheels, Node 3 tarballs. |
| Twice fresh offline scenarios | Six checks pass using untouched v2 references/protected oracles. Stdlib valid/invalid CLI; API offline wheel build/install and real loopback HTTP/schema/domain cases; Node strict compile, Node types, API/CLI invalid cases and generated tests. |
| Runtime | Python 3.12.13; API FastAPI 0.115.12, Uvicorn 0.34.2, setuptools 78.1.0; Node 22.23.3/npm 10.9.9/TypeScript 5.8.3/@types/node 22.15.3. |
| CLI inspect/check | All profiles inspect successfully and pass two additional fresh offline smoke checks. Executor receipts show runc/network-none, nonroot, no capabilities/GPU/socket and read-only dependency mounts. |
| Frozen task and restart | All three Factory tasks accept after closing/reopening controller, despite deliberately nonexistent configured image; repeated accepted resume succeeds. Protected checks use frozen environments. |
| Manifests/errors | Inference matches all three projects. API and Node conforming manifests pass; missing, malformed and unsupported dependency/lock inputs reject. Appending whitespace to each bound manifest rejects verification despite otherwise conforming reference. |
| Model context without inference | Captured mock worker and reviewer requests contain the bound profile/runtime context for each profile. No actual model calls. |
| Lifecycle regression | 15 runner tests pass. |

## Reproduction and evidence

From repository root:

```sh
python3 .scratch/.sflo/04-autonomy-environments/qa-profiles/probe.py
python3 .scratch/.sflo/04-autonomy-environments/qa-profiles/boundaries.py
python3 .scratch/.sflo/03-autonomy-review/qa_pinned.py 51479e9663f810e33031774abceca067cd761a48 -m unittest discover -s tests -p test_runner.py -v
```

[Evidence directory](qa-profiles/): `results.json`, `probe.log`, each profile's receipt/checks JSON, `boundaries-results.json`, `boundaries.log`, `runner-tests.log`, and complete executable probes. Raw initial `probe-original.py`/log/results preserve a verifier-harness TypeError: the final manifest check omitted the acceptance argument after every cold preparation, six scenario checks and three restart controls had already passed. Corrected `boundaries.py` reran the conforming verification control and tamper rejection for both packaged profiles, then passed all contexts/errors. `probe.py` now includes the correct argument for reproduction; raw failure results were not rewritten into passes.

No product defect found in this scope. CLI preparation/inspection/check are exercised directly; bound task/restart uses the public Factory/Sandbox interfaces with a deterministic no-op worker, not the model-connected CLI run. Adversarial URL/resource/cancellation/publication coverage belongs to the parallel security assessment. No maintained files, protected fixtures, rig or model runtime changed.
