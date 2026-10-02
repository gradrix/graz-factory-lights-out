# Runtime provenance correction addendum

## Confirmed identities

The actual factory default image `sha256:a8a3e0a84b0d5fab2b3b4b32e89715a7384b7af2f81b5e82d203d12828cb2578` executes **CPython 3.11.15**, locally and on the rig. Local read-only confirmation:

```sh
docker run --rm --pull never --network none sha256:a8a3e0a84b0d5fab2b3b4b32e89715a7384b7af2f81b5e82d203d12828cb2578 python --version
```

Output: `Python 3.11.15`. Task03 run `43b7647311b0` uses this image in all three `attempts/*/verification.json` check receipts; its recorded tool output independently prints 3.11.15. Root independently confirmed rig version/config. This audit did not inspect private config.

The separate local image `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc` (currently tagged `python:3.12-slim`) executes **3.12.13**. Semantic rechecks using it are supplemental target-version checks, not reproductions in the factory's execution image. Earlier host semantic probes explicitly used installed uv **3.12.12**; those are a third interpreter identity.

## Earliest located assumption and affected reports

Scoped Git history shows `docs/operations.md:45` has correctly documented 3.11.15 and image a8a3 since `b9d3765` (2026-10-02 09:24 +0300). The earliest misleading alignment wording located in this audit is commit `3cef43d` (12:09 +0300), introducing `semantic-bounded-receipt.md`: “matching-version” and “actual supported runtime” conflate the intended 3.12+ contract with factory execution. Its explicitly reported uv 3.12.12 probe is real; the alignment inference is unsupported. This is the earliest located committed wording, not proof of the first conversational assumption.

Needed documentation corrections, preserving original raw artifacts:

- `semantic-bounded-receipt.md:11,35,41`: qualify 3.12.12 evidence as supplemental intended-version checks and link this mismatch addendum. Do not relabel it as production-image evidence.
- `coding-b-semantic.md:21` and table wording “target-generated” / “target pinned-image”: distinguish host 3.12.12 or actual receipt image from production a8a3. Existing findings remain evidence at their recorded interpreter.
- `docs/evidence/autonomy-stages.md:27` and cohort summaries: explicitly state intended 3.12+ versus executed 3.11.15, and withhold runtime-conformance qualification.
- `run.md:26,46`: preserve original fixture-validation statements, add the actual factory mismatch to cohort context. A fixture validation on another interpreter does not establish execution-runtime conformity.
- C semantic collector/reports: `qa-coding-c-collect.py:21` uses local fb1118/3.12.13. Label resulting `coding-c-evidence/*` receipts accordingly. `qa-semantic-resumed.md:29` already separates local recheck identity from earlier runtime receipts; retain that distinction.
- Keep `docs/operations.md`'s 3.11.15 statement unchanged. Keep `docs/research/environment-preparation.md`'s 3.12 as an explicit future target, not a current claim. C and C-v2 `private/validation.json` already record **3.11.15** correctly; retain frozen files/manifests/objectives.

The previous timezone/UTF-8 conclusions need not automatically reverse: a direct read-only check in actual a8a3 reports UTF-8 encoding and accepts `2024-01-01T00:00:00Z` as UTC. This confirms those narrow environment behaviors only, not a rerun of all earlier semantic checks.

## Qualification consequence

C objectives require Python 3.12+ while factory execution uses 3.11.15. Current batch results are bounded behavior observations under 3.11.15 and **do not establish the stated runtime target**. Retain task03/task06 repair failures and every raw outcome. Before a future qualification, explicitly select the intended interpreter/image, record its executed version, and requalify affected evidence. No image, runtime, prompt, fixture, or raw evidence changed during this audit; no GPU/model calls.
