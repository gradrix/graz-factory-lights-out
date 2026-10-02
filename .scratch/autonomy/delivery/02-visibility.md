# Observe and control one local run

Status: accepted
Blocked by: none
Owner: /root

Contract source: docs/roadmap.md stage 1; docs/decisions/architecture/003-autonomy-route.md.

Deliver durable versioned events and a read-only watch/API/page over run/task/attempt state. Show phase, last meaningful action, heartbeat, model/container state, budgets and evidence. Keep cancellation/resume as explicitly scoped CLI controls initially; the HTTP view stays read-only. Preserve lifecycle guarantees.

Acceptance: external client observes three runs; reconnect and actual process death preserve honest state; model stall is visible; no orphan writer or duplicate accepted transition; logs remain bounded/redacted and patches/checks are reachable. Start loopback/SSH; private-network access needs authentication. Existing repair/recovery tests remain green.

Candidate: 18a274fa2e1391f744feb8d06f8eda17157ab27f
Evidence: .scratch/.sflo/02-autonomy-visibility/qa-accepted.md; rig-trials.json; rig-guardian-final.txt; coverage-final.txt. Three real Flash tasks passed (cancel/resume, SIGKILL/resume, ordinary run), each exactly one accepted event. Trials used 3c3a834; scoped startup repairs and guardian fixes independently rechecked through final candidate, including actual rig guardian tests. 33 regressions pass; subprocess-inclusive coverage 87%.
Execution run: .scratch/.sflo/02-autonomy-visibility/run.md. User authorized incremental implementation and real 5090 acceptance on 2026-10-02.
