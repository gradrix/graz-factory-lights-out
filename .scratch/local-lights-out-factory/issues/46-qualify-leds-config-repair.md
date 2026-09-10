# Qualify repair portability on leds-service configuration parsing

Type: task
Status: resolved

## Selection and baseline

Use owner-offered leds-service at 24f602c0bf7e67e781a04cd741f4c98a99ad616d.
Whitespace around configuration keys causes a valid service to be discarded and
silently replaced with default pin/port/count; empty required values are accepted.
The target is pure Python configuration parsing, independent of GPIO hardware.

## Frozen scope

Trim whitespace around comma-separated keys and values within colon-separated
services. Require nonempty pin/port/ledCount; ignore incomplete services and use the
existing string defaults (18/9000/10) only if no complete service remains. Preserve
service order, string values, last duplicate key behavior, ignoring unknown/malformed
fields, class/public interfaces, file/environment reading and cache behavior.

Two tasks: repair configreader.py and add substantive isolated pytest regressions.
Use the same model/deployment and existing generic repair protocol. Freeze independent
reference checks, original-baseline rejection and coverage checks before live calls.
Capture/preserve the whole repository including opaque UI assets. Do not claim GPIO,
gRPC, web deployment or an unattended product build from this parser qualification.

## Answer

Merged [leds-service PR 10](https://github.com/gradrix/leds-service/pull/10) at
9ab0926a9c693d6972aadd3fc009593ed1c3c88a. The same local model produced implementation,
initial tests and the reviewed correction without product-specific factory changes.
Six tests pass; original and fallback mutant are rejected; independent reference
checks pass 600 seeded cases plus edges. All 84 other original files are unchanged.

Initial acceptance missed a weak default-valued whitespace test. Recorded finding
blocks reuse. Reviewed repair added a non-default regression in one response. Final
replay adds no calls. This is supervised qualification, not an unattended score.
[Results](../leds-config-results.json) preserve costs, generated source and finding.
Both fixtures reconstruct from the pinned baseline; raw evidence remains ignored.
