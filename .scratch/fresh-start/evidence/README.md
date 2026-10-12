# Evidence

- `candidate2.json` identifies the independently checked runtime and initial documentation. Runtime files are unchanged in the final release; later edits strengthen example acceptance and record outcomes.
- `qa-candidate2.md` and its complete probe/log cover crash recovery, stale acceptance, orphan cleanup, patch application and CLI status.
- `coverage.txt`, `coverage.json` and `rig-tests.txt` record the maintained test suite locally and on the rig.
- `model-smoke.json`, `model-rollback.json` and `deployment.json` record the model setup, original-vLLM rollback and deployed runtime hashes without credentials.
- `pilot-128k/` preserves the initial on-rig scenarios exactly as run. `generated-review.md` explains why two check-passing candidates still needed repair. Repair artifacts are separate; rejected evidence is not rewritten.
- `baseline-rejections.json` shows all unfixed inputs fail acceptance.

The complete frozen QA source copies are archived here. To reproduce historical QA in its expected paths:

```sh
tar -xzf candidate1-source.tar.gz -C /tmp
tar -xzf candidate2-source.tar.gz -C /tmp
python3 qa-candidate2-probes.py
```

Run generated-review probes from the repository root after extracting candidate2. They deliberately reproduce the original rejected behaviors; exit zero means the recorded observations reproduced, not that those original deliverables are approved.
