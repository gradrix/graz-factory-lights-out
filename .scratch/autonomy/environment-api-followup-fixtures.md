# Packaged API follow-up fixture preparation

Verdict: author self-verification passed; ready for independent fixture QA. Applied s-qa at slice depth. No irreducible policy issue, target-model calls, rig changes or maintained runtime edits occurred. These isolated fixtures do not grant Stage 3 acceptance or replace prior model outcomes.

## Frozen identities

| Artifact | SHA-256 |
| --- | --- |
| Preserved original v2 private manifest | `858384ee7ca74724efe1ee4247c69cc039d88e8b53b344ef42c5f6c6d6e9989b` |
| Corrected `.gflo/environment-coding-qualification-v3/manifest.json` | `ff1ebb8b8846dcef0006f63f4afc5ff1149c941df8f4c130af098e06a6299d08` |
| Proposed `.gflo/environment-api-followup-public/manifest.json` | `1accec55480d81d4467e0d6b96b5639ca43deb7444567fa3b7862a997085be34` |
| Protected `.gflo/environment-api-followup/manifest.json` | `72a7fd6eca78d476845c07f27ea143e75fbc0581758bd1f20a6e30c3421df193` |

V3 removes only the unsupported literal `pip` README assertion from the API oracle. The 40-word minimum, new endpoint requirement, public brief and all other oracle behavior remain unchanged. Full original v2 hash mapping was verified intact. A conforming reference with correct server/test instructions and no `pip` token passes. The original timeout and genuine incorrect Uvicorn target remain recorded failures; this correction does not reclassify them.

## Fresh task and coverage

The new task adds reset-aware telemetry usage to an existing installable src-layout API. It uses preceding counter samples, window boundaries, resets, duplicate timestamp validation and stable device ordering. It is not a renamed stock allocation operation. Public source/objective remain in the proposed private publication directory until review; acceptance/reference are separate. Clean starter commit: `87e2fb41f987439ad3ef25f1b4cb216be9cab52a`.

| Check | Observed result |
| --- | --- |
| Existing routes then missing-feature starter | Required failure at absent new endpoint |
| Reference at `/input/project` and `/elsewhere/source` | Both passed offline wheel installation and real HTTP checks |
| Lost pre-window baseline; wrong reset contribution | Both rejected |
| Duplicate validation skipped outside window | Rejected |
| Direct domain mutates input | Rejected |
| Coerced integer fields | Rejected |
| Incorrect documented server target; missing generated tests | Both rejected |
| V3 correct documentation without `pip` | Passed |

All eleven expected outcomes passed. Reproduction source: `.gflo/environment-api-followup/private/validate.py`; retained evidence: `private/validation.json`. V3 additionally retains its documentation control and outcome in its own private directory. Do not rerun generators over frozen artifacts; use disposable copies for independent probes.

## Environment and limits

Actual Python 3.12.13 on approved image `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`, using unchanged approved FastAPI/Pydantic/Uvicorn/setuptools locks and existing read-only dependencies. Containers selected runc, network=none, non-root user, read-only root/binds, dropped capabilities, no-new-privileges, memory=swap 1 GiB, one CPU, 128 PIDs and bounded scratch/shared memory. Device observations were empty. Each container was removed.

Budget remains three attempts, 24 turns, 900 seconds. Every mandatory protected constraint is mapped to the public brief in `acceptance-contract.json`. Documentation minimum, endpoint and correct app target are explicit public requirements; actual command/prose quality and test meaningfulness still require semantic review. Existing images/dependencies were reused, so no cold-preparation, lifecycle/security or model-capability claim is made. Independent QA must assess these frozen candidates before target-model exposure.

## Follow-up fixture version 2: timestamp bounds

Independent QA confirmed a false pass in the first follow-up fixture: replacing `Sample.at:BoundedInt` with `Sample.at:StrictInt` passed the original oracle despite allowing negative timestamps. QA separately demonstrated the conforming reference passed an added negative-timestamp assertion and the mutant failed it.

The original private fixture remains unchanged at `72a7fd6eca78d476845c07f27ea143e75fbc0581758bd1f20a6e30c3421df193`. A new `.gflo/environment-api-followup-v2` copy adds rejection of negative/over-maximum sample timestamps, negative starts and over-maximum readings, plus valid zero/maximum timestamp controls. All are justified by the unchanged public bounds. Public source/objective, runtime, budgets and private reference are unchanged. No model exposure occurred.

Focused verification on the same approved offline runc profile passed the conforming reference and rejected the unbounded timestamp mutant at `schema/domain rejection`. Original validation records remain distinct. The corrected frozen manifest identity is reported to independent QA for recheck; this remains fixture-author verification rather than independent acceptance.

V2 private manifest: `e4cdd35d290c86aa115ae1c7e76d87acfdc5be135e6779768e0f7a0c646f9a5e` (17 bound files). Focused validation SHA-256: `91aaffeebfdd507fb720c59be22e09d125727eead8c115beb831ca98e52b5d6a`. Proposed public manifest remains `1accec55480d81d4467e0d6b96b5639ca43deb7444567fa3b7862a997085be34`.
