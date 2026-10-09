# Review consistency, blind qualification and integration

Decision: user, 2026-10-08 — "shall we do all of 3 things?" in reply to the proposed next steps after [decision 009](../../../docs/decisions/architecture/009-role-ensemble-review.md): (1) judge consistency, (2) broader qualification with repeated runs and defects not seeded by the pipeline author, (3) maintained-factory integration. Pushing was not answered at that point; the user then authorised it (2026-10-08: "push to master as frequent as possible (please do if we can)"; default branch is main), so milestones are pushed. Sequencing and design are agent-authored.

## Order and gates

1. **Consistency (dev).** All 16 review-cohort-2 cases are dev from now on (their holdout was consumed by trial 5). Add a requirement interpreter and a judge panel (below). Gate: cohort 2 16/16 correct and complete, and no blocking finding outside each case's seeded defect.
2. **Blind qualification.** Review cohort 3 is built by an independent seeding agent that receives no pipeline code, prompts or results: coding-b and coding-c reference projects (24), a mix of conforming references and single seeded objective violations of diverse kinds, each verified by the project's private acceptance check or a recorded executable demonstration. The coordinator does not read the seed descriptions or private expectations before scoring. The frozen consistency candidate runs the whole cohort twice. Gate: both runs every case correct and complete; seeded-defect findings grounded; per-case agreement between runs reported.
3. **Integration.** Only after gate 2: a maintained delivery unit that adds the qualified review as an opt-in factory stage, with its own contract, tests and rig vertical. Serving parallelism is measured separately and changes no frozen profile without its own decision.

## Consistency mechanism

- Interpreter: per unit, one request seeing only the objective and the unit's statements (no candidate, no evidence), returning a verification criterion per statement. Identical inputs give identical criteria, so a boilerplate requirement is read the same way across cases. Criteria are passed to auditors, prosecutor and judges as the reading to apply, and may be wrong; they are recorded.
- Judge panel: three independent judges with distinct framings (strict, charitable, neutral); a unit repairs only when at least two judges repair on a common statement with grounded observations; otherwise pass. Any panel member incomplete leaves the unit incomplete.
- All earlier fail-closed rules, escalation and corrections unchanged.

Failures at any gate are preserved and narrow the route; a later gate never runs on a candidate that failed an earlier one.
