# Independent semantic QA: frozen coding D

**Verdict: all 12 accepted outputs pass independent functional acceptance and generated tests; the ambiguity case correctly stops for owner input.** No critical or substantive functional false acceptance was found. Preserve the raw **12/12** result. This is not a claim of a defect-free delivery: task09 has a minor documentation error, task05 has a test portability limitation, and review quality has a confirmed false positive. Stage-wide graduation remains a separate decision.

## Frozen identity and execution

Candidate **`4346ba5`**; D fixture manifest **`da7a8d364c326a61bb8c22f0873188c0498d98213a676c23107c1d730a143d0b`**. Target runtime/profile receipt: [coding-d-runtime.json](coding-d-runtime.json). It requests coder medium reasoning, a 1024-token thinking budget and 4096 total response tokens; those are requested settings, not measured reasoning-token consumption. No later product repair is included.

Target and independent checks use image **`sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`**, independently read back as **Python 3.12.13**, `/usr/local/bin/python`; see [independent-runtime.json](coding-d-evidence/independent-runtime.json). Every captured oracle matches published `evaluations/coding-d` by SHA256. Final source identities are in [identities.json](coding-d-evidence/identities.json).

| Task | Frozen run | Raw status / attempts | Passing generated tests | Semantic coverage |
|---|---|---|---|---|
| 01-contact-import | `e0413a66083f` | accepted / 1 | 9 | CSV quoting, normalization, validate-before-skipping; supplemental PASS. |
| 02-access-report | `6b89b775e9b7` | accepted / 1 | 6 | Exact route grouping and integer nearest-rank p95. |
| 03-environment-template | `f347748fc5c8` | accepted / 1 | 6 | Single-pass dollar handling; unnecessary bound validation. |
| 04-sqlite-stock | `8bf403a00749` | accepted / 1 | 9 | Persisted ordered updates, rollback, repeated SKU, closure; supplemental PASS. |
| 05-release-digest | `42dacc4913f2` | accepted / 1 | 8 | Last occurrence before internal filtering; tests tied to /workspace. |
| 06-backup-retention | `527ccc8f6903` | accepted / 2 | 8 | Correct final retention/ties; earlier review was a false positive. |
| 07-webhook-auth | `e0add99f940b` | accepted / 1 | 9 | Timing-safe comparison, malformed Unicode and tolerance; supplemental PASS. |
| 08-markdown-index | `856e6b2558b7` | accepted / 1 | 6 | Fence rules, anchor collisions and literal-base conflicts; supplemental PASS. |
| 09-invoice-csv | `ea00b5243dd9` | accepted / 2 | 5 | Exact CSV/JSON CLI; README escaping defect remains. |
| 10-service-readiness | `37b32f16896a` | accepted / 1 | 6 | Last state/critical flags, missing required services and exact types. |
| 11-support-redaction | `1cdb5b35c11b` | accepted / 1 | 3 | Casefold, whole-value replacement and deep independence; supplemental PASS. |
| 12-artifact-selector | `ee8cb62f2474` | accepted / 1 | 9 | Numeric version order, yanked filtering and smallest-ID tie break. |
| ambiguous | `ad145000d3e7` | needs_input / 1 | — | Correct policy stop; question introduces an unstated partial-payment detail. |

## Findings requiring accurate interpretation

### Task06: reviewer false positive, not useful defect detection

Review1 calls the existing tie-break critically wrong because it asserts Python `max` returns the last equal maximum. That assertion is false: the quoted expression `max(sorted(rows,key=id),key=finished)` returns the first maximum from ascending ID order, hence the required smallest ID on tied timestamps. Original acceptance and all eight generated tests had already passed. The final two-step maximum-timestamp/minimum-ID implementation is also correct, but the additional cycle did not fix the alleged defect. The review text additionally oscillates between mutually contradictory repair suggestions.

A fresh probe verifies both the quoted old expression and final candidate choose `aa` for all six permutations of tied `zz/aa/mm` inputs; an actually wrong tuple-max control chooses `zz`. See [06-backup-retention-review-false-positive.json](coding-d-evidence/06-backup-retention-review-false-positive.json), plus preserved attempt1 verification/review. This demonstrates the repair loop operates, **not** that this D review found a genuine bug. Older B11 had genuine numeric-equality review findings and a passing final recheck, but belongs to a different frozen runtime/profile and does not establish current-D reviewer reliability.

### Task09: genuine test repair, minor documentation miss remains

Attempt1's generated CLI assertion expected raw CSV despite the required JSON stdin/stdout interface. The final test correctly compares JSON-encoded CSV bytes; implementation and independent exact-example checks preserve CRLF, quoting and exact cents. This is a genuine executable-check-driven repair, distinct from reviewer defect discovery.

README's purported JSON stdout contains doubled backslashes before `r`/`n`. Decoding that displayed JSON yields literal backslash sequences instead of CRLF; actual CLI output is correct. [09-invoice-csv-readme.json](coding-d-evidence/09-invoice-csv-readme.json) records the exact correct-output control and mismatching documented representation. This is a noncritical documentation defect, not a functional failure.

### Other bounded observations

- Task05's two CLI tests hardcode `/workspace`. All eight pass there; unchanged source mounted at `/project` has two `FileNotFoundError` errors. Record this as a demonstrated portability limitation; arbitrary checkout-path portability was not a separate frozen acceptance gate. See [05-release-digest-portability.json](coding-d-evidence/05-release-digest-portability.json).
- Tasks01/03/08 add validation of guaranteed types or bounds despite “do not invent validation.” No valid-input failure is identified. Task08's generated CLI test uses `eval` rather than JSON decoding; original acceptance independently enforces JSON. Task11's “500 values” test comment actually describes a 501-value fixture. These are minor instruction/test-quality residues, not new functional failures.
- Ambiguity asks the core refund-policy question and leaves source unchanged. However, its oldest-first option adds partial payment of the first unaffordable claim, whereas the objective says pay oldest claims in full first; it also asks routine action/payload naming. The stop is correct, but question wording should avoid suggesting unstated policy as already part of an option. See [ambiguous-question.json](coding-d-evidence/ambiguous-question.json).

## Coverage and limits

Independently read all original objectives and every terminal domain/API/CLI, generated test and README. Checked original action preservation, JSON types, error routing, input immutability, meaningful normal/boundary/rejection methods, and concrete usage. Supplemental probes cover invalid duplicate CSV records; transactional rollback after earlier changes and negative intermediate stock; persisted repeated-SKU updates; malformed Unicode signatures and exact tolerance; global heading-anchor collisions; Unicode casefold and post-return container independence. Tests use disposable databases only. Expected rejection and negative controls are recorded as verifier passes.

Fresh execution used offline Docker, read-only candidate/root filesystems, non-root user, dropped capabilities, 256 MiB, one CPU, 64 PIDs and bounded timeouts. **Earlier checks for tasks01–08 used the Docker default runtime, so they establish functional behavior but not GPU/device isolation.** After this was identified, tasks09–12, subsequent supplemental checks and runtime readback explicitly used `--runtime=runc`; commands in receipts show the boundary. No model requests, GPU workloads or target runtime changes were made by this auditor. No private configuration, credentials or raw trajectories were copied.

Compact source patches, original failed/passing verification and review receipts, fresh outputs and executable supplemental probes are under [coding-d-evidence](coding-d-evidence/). Private snapshots: `.gflo/semantic-d/<run>/`. Orchestration: `qa-coding-d-collect.py`, `qa-coding-d-extra.py`; supplemental commands are fully preserved in receipts. Monitoring has stopped after all 13 terminal outputs. No maintained product, fixture or frozen output was changed; previous B/C/paired reports remain frozen. Broader deployment, multi-service journeys and subsequent redaction fixes are outside this verdict.
