# Consistent role-ensemble review as an opt-in factory stage

Status: accepted as opt-in, 2026-10-10. Blind run 2 failed 23/24 on a temperature-0 loop; the repair (sampled escalation, 60472ae) passed blind run A 24/24. Further requalification and the rig vertical were superseded by [decision 011](011-delivery-rate-route.md); live behaviour is measured in phase 1. Originally proposed 2026-10-09.

## Choice

1. Judge consistency comes from a three-judge panel (strict, charitable, neutral framings) per contested unit; a repair needs at least two judges blocking on a common statement. A separate requirement-interpreter role was tried and removed.
2. The shared review policy carries explicit reading rules: stated input bounds are caller preconditions unless an error is required; a conditional alternative is satisfied unless its condition is specified for the added work; in the factory's test-coverage boilerplate only an error specified for the newly added behavior is "a specified rejection".
3. A third reasoning rung (65536) follows 8192 and 24576 for a role that still exhausts its budget; audit citations owned by another command are pruned when an owned one remains.
4. The qualified pipeline is ported to the maintained package as `gflo/ensemble.py` behind the existing `reviewer(workspace, task)` seam, enabled only by config `"review": "ensemble"`. The runner, acceptance receipt and repair loop are unchanged; an incomplete ensemble raises and never accepts.

## Evidence

- Gate 1 (consistency, 16 cohort-2 cases): candidate 1 with the interpreter scored 3/16 (over-long criteria left 14 units incomplete; its misreadings produced three false control repairs). Candidate 2 without it scored 13/16 (two controls still misread "specified rejection"; one prosecutor exhausted 24576). Candidate 3 (prototype 6920218) scored 16/16, with each of 19 repair units citing its case's required defect at its source line.
- Gate 2 (blind, 24 cohort-3 cases built by an independent agent; expectations unread until scoring): run 1 24/24, all 12 seeded defects across 12 classes cited at their lines, no blocking finding on 12 controls; the seeded `tests-miss-required-category` defect was still caught under the new reading rule. Run 2: 23/24 (b06 incomplete on a temperature-0 loop). Candidate 4 (sampled escalation) blind run A: 24/24.
- Integration: offline controls 16/16; replaying the stored role answers of gate 1 trial 3 and gate 2 run 1 through the maintained judging code reproduces 40/40 case decisions and every unit decision.

## Limits and remaining assumptions

- The reading rules were derived on dev cases; the blind cohort is evidence that they generalise to the same objective template, not to arbitrary objective styles.
- Python projects only (node-ts is refused). Cost per review is roughly 17–31 minutes and ~0.4M local tokens on one serving slot; units are independent, so serving parallelism is the scaling lever, measured and decided separately.
- Explorer command outputs use the maintained sandbox's bounded tail, explorers make no advisory final request, and their system prompt no longer demands at least one command. The replay shows the judging code is unchanged; it re-judges the prototype's stored evidence, so it cannot show that evidence gathered by the maintained code is equivalent. The deterministic battery is the qualified one verbatim (independent QA found and a test now pins an earlier rewritten documented-command runner that dropped heredocs and `$ ` prompts); live equivalence of explorers rests on the rig vertical.
- The judged objective is the task objective only, as in qualification; the runtime-context lines given to the worker are not split into judged statements.
- The prototype's 256 KiB expanded-report rejection is not carried over: it could only reject an otherwise valid answer because the catalog was near its own size cap.

## Consequences

The single-request `review.py` remains the default. The ensemble is the recommended reviewer for unattended Python coding runs once promoted.

## Update 2026-10-11: real repositories (agent decision)

On 16 tasks mined from two real repositories (roadmap phase 1, frozen 7cedc3c), the ensemble delivered 7. All 9 losses were the ensemble failing to reach a decision: 4 audit requests timed out, 1 audit request reached ~120K tokens against the 98K context, 4 role outputs failed validation. In 6 of the 9 the patch passes the hidden tests. Each run took 2–5× as long as with the default reviewer, and it caught no defect that the hidden tests or the default reviewer missed. Details: `.scratch/.sflo/11-delivery-rate/run.md`.

The ensemble has used its qualification rounds. It stays opt-in and is **not** promoted: the "recommended once promoted" consequence above is withdrawn, and the single-request reviewer is the factory's reviewer. Reopening it would need serving parallelism and audit inputs sized for real repositories. Both are out of scope until the delivery rate earns phase 4.
