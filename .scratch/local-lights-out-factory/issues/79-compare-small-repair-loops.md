# Compare small repair loops before revising Work atoms

Status: resolved
Type: task

## Request

Owner authorized trying small tasks before larger systems and asked whether the
Work atom structure needs reconsideration. Prior authorship question is superseded
for this work: diagnose factory reliability, do not manually finish Importflow.

## Scope

Compare a single prepared factory atom with a minimal coding loop, using the retained
failed Importflow parser, identical requirements, admitted execution image, independent
checks, pinned model and six-response/16K-total/6K-output limits. Preserve histories.
This is a composite diagnostic, not an isolated causal ablation or deployment qualification.

## Comments

Retained parser reproduces empty-input failure in isolated broker. Keep the complete
parser gate to catch repair regressions; further input minimization would remove the
preservation behavior being measured. Preparation v1 failed strict Python tuple parsing
before any inference; corrected v2 uses JSON contract parsing. No historical run reset.

## Answer

Both arms halted after six responses. Factory 20,013 tokens; minimal 11,440.
Minimal repeated the same second candidate through turn six. Neither task isolation
nor the composite simpler loop rescued the retained repair. No atom-schema change
justified by this pair. Keep core contract and qualify smaller creation/repair tasks
with informative diagnostics before larger systems. See [results](../repair-comparison/README.md).
