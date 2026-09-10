# Ground repair calls in revision-bound definitions

Type: task
Status: ready-for-agent
Blocked by: 67

## Evidence

After the reasoning-only truncation fix, the first fresh full-feature follow-up
continued past truncation but generated tests with invented createPlayer/createGame
signatures. It fixed one call after feedback and failed on the next. Existing source
reads and failure-local test windows did not establish sufficient interface grounding.

## Scope

Inspect retained manifests and diagnostics to establish which called definitions
were visible, discoverable, omitted or never requested. Reproduce the exact missing
information with CPU fixtures before changing behavior. Evaluate a generic bounded
bridge from a failed call to a revision-bound Python definition, using the existing
repository navigation seam. Do not hardcode SQLite, ai-gamer paths or helper names,
introduce unrestricted source access, weaken gates, or change model weights.

Preserve immutable source identity, read authority, window count/byte/token ceilings,
exact-edit binding and historical profiles. If a runtime change is justified, qualify
it with fresh finite work using unchanged requirements and independent tests; retain
all failures. Record whether it supplies missing context or merely changes prompting.
