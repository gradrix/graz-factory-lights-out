# Improve planner read and coverage recovery

Type: task
Status: ready-for-agent

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
