# Consistent role-ensemble review as an opt-in factory stage

Status: proposed, 2026-10-09 — pending blind run 2, the rig test suite and the rig vertical; promotion to `main` follows only when those pass. Decision makers: user asked for judge consistency, broader blind qualification with repeated runs, and maintained integration, continuing automatically (2026-10-08, "shall we do all of 3 things?"); design, sequencing and this record are agent-authored. Originating units: `.scratch/.sflo/09-autonomy-review-qualification/`, `.scratch/.sflo/10-autonomy-ensemble-integration/`.

## Choice

1. Judge consistency comes from a three-judge panel (strict, charitable, neutral framings) per contested unit; a repair needs at least two judges blocking on a common statement. A separate requirement-interpreter role was tried and removed.
2. The shared review policy carries explicit reading rules: stated input bounds are caller preconditions unless an error is required; a conditional alternative is satisfied unless its condition is specified for the added work; in the factory's test-coverage boilerplate only an error specified for the newly added behavior is "a specified rejection".
3. A third reasoning rung (65536) follows 8192 and 24576 for a role that still exhausts its budget; audit citations owned by another command are pruned when an owned one remains.
4. The qualified pipeline is ported to the maintained package as `gflo/ensemble.py` behind the existing `reviewer(workspace, task)` seam, enabled only by config `"review": "ensemble"`. The runner, acceptance receipt and repair loop are unchanged; an incomplete ensemble raises and never accepts.

## Evidence

- Gate 1 (consistency, 16 cohort-2 cases): candidate 1 with the interpreter scored 3/16 (over-long criteria left 14 units incomplete; its misreadings produced three false control repairs). Candidate 2 without it scored 13/16 (two controls still misread "specified rejection"; one prosecutor exhausted 24576). Candidate 3 (prototype 6920218) scored 16/16, with each of 19 repair units citing its case's required defect at its source line.
- Gate 2 (blind, 24 cohort-3 cases built by an independent agent; expectations unread until scoring): run 1 24/24, all 12 seeded defects across 12 classes cited at their lines, no blocking finding on 12 controls; the seeded `tests-miss-required-category` defect was still caught under the new reading rule. Run 2: pending.
- Integration: offline controls 16/16; replaying the stored role answers of gate 1 trial 3 and gate 2 run 1 through the maintained judging code reproduces 40/40 case decisions and every unit decision.

## Limits and remaining assumptions

- The reading rules were derived on dev cases; the blind cohort is evidence that they generalise to the same objective template, not to arbitrary objective styles.
- Python projects only (node-ts is refused). Cost per review is roughly 17–31 minutes and ~0.4M local tokens on one serving slot; units are independent, so serving parallelism is the scaling lever, measured and decided separately.
- Explorer command outputs use the maintained sandbox's bounded tail, explorers make no advisory final request, and their system prompt no longer demands at least one command. The replay shows the judging code is unchanged; it re-judges the prototype's stored evidence, so it cannot show that evidence gathered by the maintained code is equivalent. The deterministic battery is the qualified one verbatim (independent QA found and a test now pins an earlier rewritten documented-command runner that dropped heredocs and `$ ` prompts); live equivalence of explorers rests on the rig vertical.
- The judged objective is the task objective only, as in qualification; the runtime-context lines given to the worker are not split into judged statements.
- The prototype's 256 KiB expanded-report rejection is not carried over: it could only reject an otherwise valid answer because the catalog was near its own size cap.

## Consequences

The single-request `review.py` remains the default. The ensemble is the recommended reviewer for unattended Python coding runs once promoted.
