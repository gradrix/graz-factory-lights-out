# Independent QA: failed Stage 3 Node run

## Verdict

Frozen run `00cab7ec321d`, runtime `25f75c3`, remains **interrupted at the 900-second wall limit, attempt 1, pending request turn 15**. No acceptance or independent local reviewer decision occurred. Original cohort outcome remains **1/3 accepted**. This audit does not convert a timeout into acceptance.

**Concrete remaining defect: required documentation was never written.** README remains the short starter describing only compilation and `total`; it has no new report usage, error behavior, runnable CLI example, or required 40-word explanation. The missing documentation is a justified contract defect. However, the untouched oracle fails earlier on a separate false rejection described below; it never reaches its documentation assertion in this candidate.

## Protected oracle false rejection

The oracle treats any stderr containing the substring ` at ` as a stack trace. For 1001 events, the correct CLI rejection says `events must be an array of at most 1000 events`; the words ` at most ` trigger this assertion. Exit status is correctly 2, stdout empty, and stderr is a single ordinary error message. The candidate therefore fails the frozen oracle for a checker defect as well as having unfinished documentation. There was no model-time protected-check invocation; this failure was independently reproduced after interruption. A diagnostic checker copy uses a line-anchored stack-frame predicate `/^\s+at\s/m`; the original remains untouched.

## Semantics and tests

The final report implementation validates the event list and threshold, rejects invalid event objects, booleans/nonintegers/out-of-range durations, empty/non-ASCII service names and unknown outcomes. It validates every event before filtering, groups with Map (including prototype-like names), sorts with ordinary string comparison, counts outcomes, computes exact bounded totals (maximum 10^12), and uses ceiling averages. It constructs new rows without mutating input. ASCII control characters are valid under the stated ASCII requirement and are accepted. `total` and CLI code preserve baseline behavior; no new material semantic defect was identified.

Five meaningful generated tests cover normal grouping/filtering/order and mutation, empty reports, 1000 events and large sums, ceiling averages, invalid values/ranges/ASCII and validation before filtering, preserved total/unknown action, and CLI JSON/error behavior. Paths derive from the test file location rather than a fixed workspace mount. An empty `describe` suite adds no coverage and can be removed as minor residue. The extraneous `stderr` option does not redirect child-process output; the tests still inspect captured stderr and pass. Neither is a blocking behavior defect.

## Trajectory

The frozen trace contains 15 requests, 14 responses, and 18 tool events. Turn 15 has no response before interruption. No protected `check` call is present.

- Turns 1–3 repeatedly inspected a small baseline; an attempted read of protected acceptance files failed as intended.
- Turn 4 wrote the feature. Turn 5 compile failed because a boolean validation helper did not narrow `unknown` values; subsequent explicit casts after checks fixed compilation.
- Turns 6–8 repaired/checked ASCII validation and compiled successfully.
- Initial tests imported nonexistent `{node}` from `node:test`; the model inspected exports and rewrote tests.
- `node --test tests` and `tests/` treated the directory as a module and failed; plain `node --test` or an explicit test file worked.
- The CLI assertion read child-process error `.code` instead of `.status`. Turns 12–13 inspected the error; turn 14 corrected it and all five tests passed.

The remaining failure is incomplete delivery within the frozen budget, with avoidable verification-tool mistakes consuming turns. There is no evidence of an endpoint/domain regression driving the timeout. No measured reasoning-token claim is made.

## Minimal recovery

Start a separately identified continuation from the frozen candidate. Write the missing README with location-independent offline compilation, `node --test`, JSON stdin/stdout examples for report, validation and CLI exit-2 behavior. To satisfy the frozen checker without changing behavior, reword “at most 1000” to “no more than 1000”; this is a compatibility workaround, not a semantic fix. Then run the original protected oracle and fresh review/recheck. For future fixtures, use a stack-frame detector instead of the arbitrary substring check and version that oracle correction. Build in a disposable copy if compiled `dist` artifacts are not intended deliverables. No algorithm rewrite or dependency change is indicated. Keep original timeout, budget and cohort score unchanged.

## Independent execution evidence

Sibling `qa-model-node-failed/run.py`, `probe.cjs`, and `receipt.json` reproduce the checks and freeze input hashes. The sandbox uses the original image `sha256:88f8ba583a884279252779bbe221bf1ff2c61cf236cc973f8ca97676ae6d07f0`, explicit runc, no network, non-root user, read-only frozen inputs and approved prepared `/node_modules`, one CPU, 512 MiB memory, and a 180-second process bound. Only disposable `/tmp` copies are compiled or changed. No model calls or maintained-source changes occurred.

Observed results: strict compilation and all five generated tests pass after relocation to `/tmp/project with spaces`; 200 seeded independent report comparisons including prototype-like names and ASCII control characters pass without mutation. The frozen original oracle fails its broad ` at ` check. A README-only repair still fails that same check. With repaired README and only the stack-frame predicate corrected in a disposable oracle copy, the full gate passes. With repaired README plus harmless error-message rewording, the untouched original oracle passes. These controls separate the genuine documentation omission from the checker false rejection; all originals remain frozen.
