# Independent QA: known-case paired repair results

**Verdict: both accepted repairs are semantically valid; both none arms remain failed.** This is a successful repair demonstration on two already-known failures, not unseen qualification or proof that the reasoning setting alone caused the improvement. No model requests or GPU operations were made during this audit.

| Case / requested profile | Frozen run | Raw outcome | Independent acceptance / default discovery | Recorded wall time / coder requests |
|---|---|---|---|---|
| Bit fields / none | `802dd724143a` | exhausted | FAIL / zero tests | 34.524 s / 17 |
| Bit fields / medium, 1024 | `068017f2ddf1` | accepted | PASS / 3 tests pass | 64.525 s / 6 |
| Luhn / medium, 1024 | `1c5a06cc463b` | accepted | PASS / 4 tests pass | 319.129 s / 21 |
| Luhn / none | `fb5a89c634de` | exhausted | FAIL / 2 of 3 tests fail | 39.635 s / 12 |

## What actually changed

- **Bit fields:** adds an empty `tests/__init__.py`, making the three meaningful regression methods discoverable by the contract-required default command. Domain, API, CLI and original acceptance are byte-identical to the frozen failed source. The negative control removes this marker only in disposable container storage: the minimum-test assertion fails again. Correct delivery passes the same assertion and tests.
- **Luhn:** preserves the original correct algorithm/API/CLI and repairs wrong test expectations: `7992 781` appends to `79927810`, while `7992 781-2` is invalid. README examples now correctly use `49927817` and `4992 781-7`. The new fourth test checks atomicity and a large boundary. Exact documented success and rejection examples were executed through the CLI. An independent positional checksum oracle agrees on 1,000 zero-padded append inputs and 10,000 check inputs. A deliberately broken checksum function is rejected by the delivered tests. This expected negative-control failure is a passing verifier outcome; the overall probe exits zero.
- Both none-arm workspace patches are empty. Original failure outcomes were reproduced. Frozen oracle files are unchanged in all four arms; this was repair of delivery obligations, not weakening acceptance.

## Requested profile versus measured behavior

The actual request receipts show `reasoning_effort=medium`, `enable_thinking=true`, top-level `thinking_budget_tokens=1024`, and `max_tokens=4096` in both thinking arms. None arms request `reasoning_effort=none`, disable thinking and omit its budget. Reviewer profile and per-arm limits remain shared; the order was bit-fields none then medium, Luhn medium then none, with no initial failure explanation supplied to either arm.

Usage reports prompt/completion/total tokens and cached prompt tokens, **without reasoning-token counts**. The receipts therefore establish what was requested, observed wall time, request counts and accepted outputs. They do not establish that the server enforced exactly 1024 thinking tokens, consumed any particular reasoning count, or that this small, sequential, cached experiment generalizes. The successful Luhn arm was substantially slower and made more requests. Fixed-profile unseen evaluation remains necessary.

## Identity, execution and scope

All offline reruns used pinned image `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`, verified Python **3.12.13**, matching the paired target receipt. Initial frozen candidate hashes are `9bf105498bc2780ad476b0cf669e88b2fd15c7e5af14602263e6f39bcb529520` (bit fields) and `cc6a178e8d61d2a51c8754fab3c6269649bb977301515aecb07cca25b3a3ff89` (Luhn). Final file/workspace hashes, source patches, original verification/review receipts and fresh outputs are in [repair-reasoning-evidence](repair-reasoning-evidence/); [summary.json](repair-reasoning-evidence/summary.json) maps all four runs to identities and requested profiles.

Reproduce collection/checks with `python3 .scratch/.sflo/03-autonomy-review/qa-repair-reasoning-run.py`; complete supplemental source and executed commands/results are in `repair-reasoning-evidence/supplemental.py` and each thinking arm's `*-supplemental.json`. Containers had no network/GPU, read-only candidates/root filesystem, dropped capabilities, non-root execution, 256 MiB memory, one CPU, 64 PIDs and 35-second inner timeouts. Only temporary sandbox copies/memory were mutated for negative controls. No maintained code, original candidate or fixture was edited. Product candidate `49559e9` and any new D trial are outside this semantic audit.
