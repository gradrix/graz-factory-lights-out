# GFLO handoff — await the RTX 5090 target

## Current state

Research and architecture planning are recorded in [the map](map.md). Decisions through [Prototype the reference architecture](issues/11-prototype-the-reference-architecture.md) are resolved as design choices, not hardware-tested feasibility claims. [Plan the staged implementation and validation](issues/12-plan-the-staged-implementation-and-validation.md) contains the proposed stage sequence and remains claimed pending final agreement.

The HTML lifecycle demo is a throwaway in-memory simulation, not a running factory. JavaScript syntax and Git whitespace checks have passed. Browser behavior, real inference, isolation, durable recovery, and coding capability have not been validated here. No production factory implementation or model runtime has been installed as part of this checkpoint.

## Latest user constraint

The user is away from the RTX 5090 until later and considered temporary inference on this Acer or an M3 Pro MacBook. Recommended course: preserve this checkpoint and wait for the intended GPU target for the first model-capability experiment. A temporary backend may later help with transport/plumbing tests, but its results must not qualify the intended RTX 5090 model/runtime profile. Do not install a temporary model merely to keep activity going.

## Resume path

1. Make this Git checkpoint available to the destination checkout. A local commit alone is not available from origin; pushing or another transfer is a separate action. Git transports repository artifacts, not local conversation/session state or credentials.
2. Read this handoff, the map, and the staged-plan ticket. Preserve the accepted defaults: small worker views; tests-first dynamic diagnosis/repair; scheduler-owned work and evidence; on-demand planning; no SFLO/Gas City runtime dependency; profile-driven output languages.
3. Confirm the proposed first implementation scope: Stage 0 target verification and Stage 1 durable worker loop plus the twelve-task live pilot. Do not implement later layers before pilot evidence.
4. Locate the actual GPU host and endpoint; inspect driver/runtime/checkpoint/tokenizer, memory and enforced execution controls. Previously researched model/backend recipes are candidates, not verified local installations. Do not assume the destination machine is already provisioned or that the checkpoint named in research is available.
5. Create bounded implementation tasks for the first slice, then build/test the durable loop. Use deterministic doubles for mechanics only and record real-model evidence separately. Retain failed pilot results and revise context/tool/task policies before expanding.

No push, deployment, or host migration is implied by this handoff. Publication authority for generated products is unchanged. The benchmark thresholds are versioned experimental targets, not claims already achieved.
