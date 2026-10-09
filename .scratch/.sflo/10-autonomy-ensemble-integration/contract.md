# Maintained executable ensemble review (opt-in factory stage)

Decision: user, 2026-10-08 — "shall we do all of 3 things?" (third item: maintained factory integration), with "push to master as frequent as possible" and continue automatically. Design, sequencing and acceptance below are agent-authored.
Predecessor: [review qualification](../09-autonomy-review-qualification/run.md); qualified candidate prototype 6920218 (gate 1 16/16 grounded; gate 2 blind run 1 24/24 grounded; run 2 pending at contract time). Implementation may proceed offline while run 2 is pending; maintained promotion requires gate 2 to pass.
Base: main, maintained runtime 92deaab.

## Scope

Port the qualified role-ensemble review into the maintained package as `gflo/ensemble.py`, behind the existing reviewer seam `reviewer(workspace, task) -> {decision, findings, question}` so the runner, acceptance receipt and repair loop are unchanged.

- Pipeline equals the qualified candidate: evidence battery (tests from a writable copy, documented-command runner) → three tool-using explorers (tester, adversary, docs) → union catalog with head/tail bounds and segments → sentence statements in ≤400-char units → per unit: audit in chunks of 8 commands, prosecutor, and when contested a strict/charitable/neutral judge panel needing ≥2 judges on a common statement; up to 2 quoted corrections; reasoning ladder 8192 → 24576 → 65536; foreign audit citations pruned; same POLICY text and reading rules.
- Commands run through the maintained `Sandbox` (pinned image, bound environment, offline, read-only candidate mount, resource limits). Candidate tree identity is checked before and after the review; any change fails the review.
- Output mapping: each panel-backed blocking finding becomes a runner finding (severity, path, line, evidence = model inference plus cited observation excerpts, repair = the violated statement to satisfy), bounded to the runner's validator limits. `needs_input` carries the judge question. An incomplete ensemble raises, so the run is interrupted and resumable; it never accepts.
- Full evidence (catalog, every role request/response, unit results) is written under `<run>/review-evidence/<timestamp>-<id>/` (the reviewer seam receives the workspace, not the attempt directory; the runner is unchanged), and the accepted receipt keeps binding `review.json`.
- Recorded deviations from the prototype, none in judging: explorers stop at their first no-tool reply and make no advisory final verdict request (the qualified pipeline never used it); command output is the maintained sandbox's bounded 16 KiB tail instead of the prototype's nonce-attested head; command receipts are the maintained guard's, not the prototype ledger.
- Opt-in only: config `"review": "ensemble"` (default `"single"` keeps today's `Reviewer`). No frozen inference or sandbox profile changes. No serving-parallelism change.

## Acceptance

1. Offline controls in Docker: unit tests for statements/units, catalog bounds, audit validation/pruning, panel decision, escalation ladder, correction, output mapping and validator compatibility, candidate-identity failure, incomplete → raise, config opt-in wiring; full existing maintained suite still passes.
2. Equivalence: the maintained judging functions reproduce the qualified candidate's recorded decisions when replayed over stored role answers from gate trials (no model calls).
3. Rig vertical (`ops/rig_ensemble_vertical.sh`): real `gflo run` CLI runs with `"review": "ensemble"`, the live worker and the approved python-stdlib environment, on coding-d tasks 05-release-digest and 09-invoice-csv. A live worker cannot be forced to produce a defective first candidate, so: each run must end with ensemble review evidence and either accepted or an honest recorded failure; every ensemble repair finding must reach the next attempt as `previous.review`; accepted candidates are independently checked against the coding-d private references. Seeded-defect detection is evidenced by gates 1-2 and the 40/40 replay; repair-loop wiring by the offline runner test. Evidence linked from the run record.
4. Docs: `docs/architecture.md`, README/config docs, decision record for promotion; delivery map and unit updated.
