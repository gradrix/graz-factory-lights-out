Contract source: docs/roadmap.md stage 1; docs/decisions/architecture/003-autonomy-route.md.

Deliver durable versioned events and a read-only watch/API/page over run/task/attempt state. Show phase, last meaningful action, heartbeat, model/container state, budgets and evidence. Keep cancellation/resume as explicitly scoped CLI controls initially; the HTTP view stays read-only. Preserve lifecycle guarantees.

Acceptance: external client observes three runs; reconnect and actual process death preserve honest state; model stall is visible; no orphan writer or duplicate accepted transition; logs remain bounded/redacted and patches/checks are reachable. Start loopback/SSH; private-network access needs authentication. Existing repair/recovery tests remain green.

