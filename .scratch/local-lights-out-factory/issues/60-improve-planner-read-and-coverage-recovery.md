# Improve planner read and coverage recovery

Type: task
Status: resolved

## Evidence

Window planner navigation-v3 eventually quoted the actual function body, but needed
five turns over two attempts. Complete feature v4 exhausted planning after a repeated
read and then a proposal that omitted a requirement. See window-feature-qualification.
The controller rejected the invalid proposal; no work was authorized from it.

## Scope

Investigate a clearer read-result representation and bounded recovery from redundant
reads and incomplete plans. Measure against retained failures and successful complete
features, with the same model and aggregate budget. Consider retaining already obtained
revision-bound context across retries and targeted schema feedback within remaining
turns. Do not silently add tasks, invent policy, weaken requirement coverage, expand
scope or reset historical attempts. Preserve source-free product-policy review.

Prefer a tested protocol/state change to accumulating task-specific prompt advice.
Record first-run and repeated success rates rather than reporting only a best run.

## Answer

Implemented persistent bounded read context, direct file/range labels, recovery within
remaining turns and specific missing-requirement feedback. Omitted request identity is
bound by the controller; explicit wrong identities still fail. Clean discriminated
schema errors no longer echo abbreviated input. Legacy and source-free review behavior
remain unchanged. No extra attempts, tasks or policy are supplied.

Final frozen campaign: all 6 planners succeeded in their first attempt (2 turns each);
all 3 navigation rationales correctly quoted return 41; 2/3 complete features accepted.
The remaining worker failed its preservation gate. Intermediate failed runs are retained
in [qualification evidence](../planner-recovery/README.md). Full Docker regression plus
new targeted tests and historical replay pass. Continue with issue 61; issue 63 records
the owner's reliability-first, larger-specialist-budget comparison preference.
