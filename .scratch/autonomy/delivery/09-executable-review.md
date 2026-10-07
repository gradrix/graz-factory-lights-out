# Read-only executable local-review discriminator

Status: open — per-requirement units trial3 3/4; successor not yet contracted
Owner: /root coordinator, isolated builder and independent QA/security
Depends on: accepted discovery08/b13d22e; maintained runtime92deaab unchanged
Decision: .scratch/autonomy/issues/09-executable-review.md
Execution: .scratch/.sflo/09-autonomy-review-evidence/run.md
Contract: .scratch/.sflo/09-autonomy-review-evidence/contract.md sha256 3f7f503d411db873386eea9a24f3b2e2d165cde1e881ab25835341f97365a31f
Isolation: /home/gradrix/repos/gflo-review-evidence-prototype, prototype/review-evidence-20261004

Last question: could a small finalization assignment diagnose the four known cases from frozen public inputs and captured execution evidence without fabricating observations? One fresh final-only request per case; no new candidate probes. Exact references establish provenance, not entailment. No maintained promotion.

## Preserved predecessors

- [Initial executable review](../../.sflo/09-autonomy-executable-review/run.md), contract1fe3c4763dd4e1ee6d3b280619dcbce4ac1814d7253dbbba5c1d8d6f47f959d1, prototype37b7f1d:1valid correct repair,3incomplete outputs.20requests/25commands.
- [Two-phase protocol](../../.sflo/09-autonomy-executable-review-protocol/run.md), contractf4381c22e730f53bd5bab1af93e4794aa4c83fe0ce31c2a1a2767fc9a51a076f, prototype847f90e:4valid correct classifications, stricttruth FAIL for unexecuted-suite claim.26requests/33commands. All evidence immutable; no rescoring.
- [Evidence finalization](../../.sflo/09-autonomy-review-evidence/run.md), contract3f7f503d411db873386eea9a24f3b2e2d165cde1e881ab25835341f97365a31f, prototypec3673ba: 3/4 classifications; case04 false acceptance. Every fresh final request exhausted the frozen 1024-token thinking budget; three emitted an empty pass. Case01 grounded without the unexecuted-test claim. 4requests/0commands. [Assessment](../../.sflo/09-autonomy-review-evidence/qa-trial.md).
- [Per-requirement units](../../.sflo/09-autonomy-review-units/run.md), contracts b795a7bd… and 9ab40af0…: trial1 harness failed closed (0 requests); trial2 0/4 complete at 1024 thinking with exhaustion fail-closed preventing a false pass; trial3 at 4096 thinking 3/4 — case04 A6 judged the README example present without consulting captured failures. User chose this route 2026-10-07 with direction to maximise autonomy and scalability.

[Decision basis](../../../docs/decisions/architecture/008-planning-pilot-outcome.md). Each passing experiment permits only the next scoped qualification decision, not general reliability or autonomous production claims.
