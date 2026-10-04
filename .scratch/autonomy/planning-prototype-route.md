# Smaller planning discovery route

2026-10-04. Read-only addendum to [planning-frontier.md](planning-frontier.md). Unit07 remains active;92deaab is frozen for independent review. **No implementation, model/rig call or new authority follows from this proposal.**

## Recommendation

Yes: a disposable, serial driver around the existing Factory can answer whether decomposition looks useful on **one or two realistic increments before building maintained parent-plan state**. Revise the earlier route accordingly. This pilot cannot qualify Stage5, durable parent resume, parallel merging or autonomous acceptance authoring. Preserve the later six-case gate for a candidate that earns implementation.

Use two fresh small projects if feasible: an atomic CSV-ledger import plus report CLI, and a packaged API change spanning domain validation, persistence and HTTP behavior. Independently freeze source, precise requirements, milestone/full acceptance, reference controls and environment before exposure. These must be new discovery cases; do not later relabel them as unseen members of the six-case cohort.

## Disposable orchestration

One process, one shared model client/budget, one arm-specific private directory; no new production scheduler or parent database. Write a frozen experiment contract, plan JSON and append-only event/usage journal outside worker mounts.

1. Direct arm runs the full increment through one existing Factory task.
2. Decomposed arm makes one planner request proposing **exactly two ordered tasks**, followed by one fresh-context plan review. Planner maps accepted requirement IDs to tasks and states the interface dependency; it cannot invent checks, packages or product policy. The fixed controller validates coverage/dependency order and records the approved plan before dispatch. Invalid/unsupported plans fail the arm; do not rescue them with uncharged human rewriting.
3. Run task1 with Factory using independently frozen milestone checks, then verify its acceptance/patch hashes. Materialize that accepted full workspace in a fresh disposable Git repository and make a local checkpoint commit; this is the clean source for task2. Bind the source run/candidate/checkpoint IDs. Do not mutate task1's accepted workspace or original source repository.
4. Run task2 from that exact checkpoint. Apply the same independent whole-increment checks/review to the final candidate as in the direct arm, with prior behavior, generated tests and docs required. An intermediate pass is never an increment pass. Retain both intermediate and final candidates on failure.

This avoids implementing patch merging: task2 edits a complete snapshot containing task1's accepted changes. Confirm copy/file types, modes, content fingerprint and private Git base before dispatch. Reject a changed checkpoint. The result tests serialized handoff/decomposition, **not autonomous conflict resolution or general integration**. No writeback, rebase, parent resume or replanning in this first pilot. Interruption preserves evidence and ends that arm; restarting the arm is a new labeled experiment, never free budget recovery.

Keep acceptance proposal/review distinct from implementation: independent authors supply executable milestone/full oracles; planner and reviewer see public requirements and criteria, not hidden oracle/reference code. Both arms receive the same public milestone information and final acceptance standard. Stage-specific checks are a documented harness aid, not evidence the model can author sound acceptance or discover every dependency itself.

## Minimal fair budget mechanism

The existing `ModelWorker.request` is the useful seam: worker turns call it; `Reviewer` and `assess_question` also call it through the same client. A **private subclass/wrapper**, supplied to existing Factory/Reviewer interfaces, can gate every `/v1/chat/completions` request without copying the worker loop. Planner and plan review must use that same wrapper. The harness must forbid bypass clients.

Before transport, atomically reserve one request in the local journal and check a shared absolute deadline. Failed HTTP requests, malformed outputs, reviews and question assessments still consume a request. A budget exception ends the arm and is recorded alongside the unchanged Factory interrupted/exhausted status; never relabel a partial child as accepted. Fresh child tasks cannot reset the wrapper's counter/deadline.

For this pilot, freeze **equal request-count and wall ceilings plus the same per-call output cap**, e.g.48requests/1800seconds and4096output tokens per request, with the existing model/profile and one active request. Planning/review overhead is charged to the decomposed arm. Preserve actual reported prompt/completion/cached-token usage as measurements. Do **not** claim the earlier proposed32,768-total-token cap is implemented by counting turns: usage can be missing, reasoning accounting needs verification, and reserving4096tokens then never reclaiming would reduce that ceiling to only8calls. A hard aggregate-token budget is optional for this directional pilot; either implement conservative reservation/reconciliation against verified server usage with failed calls charged at their reservation, or explicitly omit the claim. Never estimate unreported usage as zero.

The wrapper can shorten request timeouts, but socket inactivity timeout is not an outer wall deadline. A supervising process must enforce the common arm deadline and bounded existing cleanup, prevent success publication after expiry, and refuse to launch another arm while owned cleanup or model-request termination is uncertain. Cleanup time is recorded separately and bounded identically. Do not assume killing a client proves the serving slot is idle. Shared request budgeting alone cannot enforce these lifecycle facts.

Use one fresh context per assignment; alternate arm order across two cases, preserve cache/latency observations, and do not feed either arm the other's output. Any human clarification/plan repair counts as intervention or stops the arm under the frozen rule. Equal ceilings mean equal available resources, not equal consumed work.

## Harness checks required before calls

Use controlled clients/workers and disposable repos to show: planner, implementation, code review and question assessment all debit one pool; denial happens before an extra request; transport failure and child restart cannot replenish credit; deadline/cancellation stops dispatch and leaves no accepted parent result; changed checkpoint/patch binding refuses; task1-pass/task2-or-full-check-fail stays an increment failure; original source and previous accepted candidate remain unchanged. These are small executable harness controls, not a maintained parent framework.

Do not approximate independent full acceptance, exact source/environment identity, authority separation, shared budget debit, cleanup, or final candidate integrity. Those determine whether the paired result is meaningful and safe. Durable parent scheduling, arbitrary DAGs, parallel conflict repair, browser adaptation and release publication can be honestly excluded from this pilot. Start with stdlib/API profiles to avoid making browser-to-candidate binding a prerequisite for the planning question.

## What the pilot can decide

Compare complete accepted outcomes, missed requirements, substantive human interventions, calls/tokens, latency and concrete failure causes. With only one or two pairs, report examples/direction and limitations, not an accuracy rate or demonstrated superiority. If decomposition merely adds overhead, drops requirements or needs manual plan repair, keep it advisory and adjust task boundaries. Do not respond by adding more agents.

**First maintained slice:** after this discovery, a shared request/deadline budget for the existing single-task path is the smallest independently useful production change—even if planning proves unhelpful. It should cover implementation, review and question assessment, persist charged reservations across cancellation/resume, expose exhaustion clearly and preserve cleanup. That durability cannot be claimed from an in-memory prototype wrapper. Do not add parent-plan state merely to ship this budget seam, and do not call that slice planning/delegation. Once the pilot shows a useful split and concrete handoff needs, implement only the parent state/integration behavior those failures justify, then run the independent six-case Stage5 comparison.
