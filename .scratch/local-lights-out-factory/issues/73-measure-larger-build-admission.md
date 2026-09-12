# Measure larger build admission

Type: task
Status: resolved

## Question

Can the current snapshot/execution path admit the factory's own committed runtime
and test suite? Measure a fixed real commit, retain exact content identities, prove
bounded context still works, and exercise both legacy SourceBundle construction
and revision-bound execution selection without enlarging their limits. Distinguish
admission failure from execution failure. Use the owner's first larger workload to
choose the subsequent versioned execution/dependency qualification; do not claim
large-system readiness from repository indexing or this admission probe.

## Answer

The fixed factory runtime alone exceeds the adapter: 34 files/381,820 source bytes.
Runtime plus tests/config is 65 files/708,963 bytes. Both legacy bundle construction
and revision-bound execution selection reject runtime, tests and full build; bounded
context succeeds. No large build ran. [Evidence](../large-execution/README.md).
A versioned isolated execution-input path plus workload-specific dependencies is
required. The owner's first larger system/repository/stack is the open product choice
for the next qualification; it is not resolved by increasing prompt limits.
