# Ground repair calls in revision-bound definitions

Type: task
Status: resolved
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

## Answer

Audited all seven retained generation requests and bound manifests. Both helper names
and definition locations were indexed, but neither definition was shown or requested.
The repair view showed the failing caller; its last response fixed createPlayer from
the error message and left the invented createGame call for final validation to reject.
No window omission or token-limit exhaustion explains the missing definitions. The
definition listing is truncated, but both relevant names are included.

A portable CPU fixture reproduces the missing-callee assertion through real window
projection. An experimental unique qualified-name lookup supplies 594 bytes of new
source within existing bounds; generic names and authority/staleness checks pass.
It still omits the next helper. This establishes feasibility and missing information,
not successful model repair. No runtime behavior or historical profile was changed.

[Audit, reproduction, measurements and decision](../definition-grounding/README.md).
The resulting prospective implementation/qualification is
[Qualify bounded failed-call definition context](69-qualify-failed-call-definition-context.md).
Worker read retention also resets across attempts in this run, but retaining the
requested addMoves window cannot supply the never-requested helper definitions.
