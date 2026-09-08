# Run the twelve-task live pilot

Type: task
Status: resolved
Blocked by: 13, 18

## Scope

Run the twelve-task workload defined by the accepted evaluation ticket with the actual RTX 5090 profile, serial inference and small Worker views. Include coding, repair, consumer migration and requirements-derived tests.

## Acceptance

Preserve exact workloads, code/profile identities, raw Attempts, token/context accounting, latency, VRAM and trusted outcomes, including failures. Compare serving configurations on useful verified coding work. Produce failure taxonomy and bounded policy fixes before expanding stages. This diagnostic pilot is not a campaign pass-rate or unattended-operation claim.

## Answer

Implemented and ran the frozen twelve-task pilot on eager and graph-enabled vLLM. Both accepted 12/12 with 11 first-Attempt successes. Preserved raw histories, workload/profile identities, token/timing/resource accounting and duplicate-read failures. Added a prospective explicit read policy and separate live check. See [pilot results](../pilot-results.md). This is development evidence, not a campaign or unattended-operation claim.
