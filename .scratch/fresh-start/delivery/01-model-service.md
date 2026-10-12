# 01-model-service

Status: accepted
Blocked by: none

## Acceptance

Pinned local Flash Coder runs on the 5090 with verified actual context, a restart policy, loopback-only access, no startup downloads and a tested explicit original-vLLM rollback. Capture model/runtime identity and smoke evidence.

Run: .scratch/.sflo/fresh-01-model-service/run.md
Candidate: 7c89eec07b0b5e1c4710d468beb5770861f35386dbafc69e5e6db44d0c515c50 (evidence/release.json)
Evidence: model-smoke.json, model-rollback.json, deployment.json, final-speed.json under .scratch/fresh-start/evidence/
