# Independent semantic QA: Stage3 stdlib model delivery

**PASS for this frozen task.** No functional false acceptance, material requirement gap or misleading example was found. This assesses one accepted expense-ledger delivery, not the remaining API/Node tasks or overall Stage3 qualification.

Frozen run `d535632d4d5f`; reported runtime candidate `25f75c3`; accepted source fingerprint `3d2822d1b4fbfa3ce460a7e828f3938e667b0b43d94370c3f6bf3f357bbaf49b`. Patch SHA256 `b17ed1410f08d8902aea1ba946928a25d627183a85cb1778d74999ec0b3552e0` and accepted verification/review hashes were independently matched. Complete captured-file hashes and commands: [qa-model-stdlib/receipt.json](qa-model-stdlib/receipt.json).

| Coverage | Independent result |
|---|---|
| Original external oracle, relocated project | PASS; original functional, type, error, mutation and documentation assertions plus 20 generated tests |
| Documented `python -m unittest discover -s tests` | PASS, 20 meaningful tests |
| Relocation and CLI routing | PASS at `/project with spaces`; absolute CLI invoked from `/tmp` |
| Supplemental ledger arithmetic | PASS, 200 seeded mixed-category/refund ledgers plus two aggregate boundaries of ±200,000,000 cents |
| Invalid shapes/types/ranges and late failure | PASS, 30 API/CLI rejection cases; exit 2, nonempty stderr, no stdout/traceback and preserved inputs |
| Runtime | Verified Python 3.12.13 in pinned image `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc` |

## Semantic assessment

Implementation validates every limit and entry before building results, rejects boolean cents/budgets, checks exact entry fields and unique nonempty IDs, and rejects unknown categories. Refunds and sums use exact integers; output includes unspent categories, sorts by Python string order and uses actual boolean `over_budget`. Whitespace-bearing category names remain valid as required by “nonempty”; no stripping or extra business rule is introduced. Existing `total`, dispatch errors and CLI behavior remain intact.

Generated tests exercise normal totals/refunds, equality and numeric boundaries, 200/201 entries, malformed fields, duplicates, boolean rejection, failed-input immutability, existing behavior and CLI success/errors. The protected reference was unnecessary: source reasoning, the frozen oracle and independent probes agree. README documents new usage, validation and error behavior, exceeds 40 words and supplies a working relocation-safe test command. Its phrase “empty limits yield []” is abbreviated; the surrounding requirement that every entry name a limit prevents interpreting this as allowing nonempty entries against empty limits.

No material abstraction or wording bloat was found. Minor cleanup opportunities are the unused direct `reconcile` import and redundant test-package/path setup; neither affects correctness or portability. The compact implementation follows the existing file style. This reviewer did not infer requirements for persistence, currency conversion, concurrency or deep independence after return beyond the specified no-mutation contract.

## Reproduction and boundaries

Run `python3 .scratch/.sflo/04-autonomy-environments/qa-model-stdlib/run.py` from the repository. Supplemental source is [probe.py](qa-model-stdlib/probe.py). All generated code executed only in bounded offline Docker with explicit `--runtime=runc`, read-only mounts/root filesystem, non-root user, dropped capabilities, no-new-privileges, one CPU, 256 MiB and 64 PIDs. No model calls, GPU workload, host execution of generated code, dependency fetch or maintained/frozen-file edits. The original model's 482.71-second single-attempt outcome and local reviewer pass are supplied run evidence; independent success above is separately reproducible.
