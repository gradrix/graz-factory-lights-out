# Independent prototype harness QA

**PASS within the bounded pre-inference scope.** Final candidate `d186b9330b7b9916e06b3807f1ea03adc02943e8`; harness SHA256 `b4e7beaab66c480f6e5f6a9a6daad6f57dbbdea6ce6b3ec4c88bafad599aafa9`. No actual model calls by QA. This qualifies harness wiring, not planning effectiveness or generated-code quality.

| Independent coverage | Result / evidence |
|---|---|
| Shared 48-call budget across planner, plan review, implementation, question assessment and code review; recreated clients | PASS, 49th denied before transport |
| Failed transport and malformed completion remain charged; changed profile and expired deadline denied before transport | PASS |
| Fixed two-task dependencies, milestone coverage, forbidden extra authority | PASS |
| Two accepted child seams followed by failing final acceptance cannot promote; original objective and fixed checks preserved | PASS, controlled Factory seam |
| Actual local subprocess supervisor deadline and cancellation | PASS, bounded short-lived processes |
| Final candidate affected rerun | 8/8 PASS; `qa-harness/independent-tests-successor-isolated.log` |
| Actual rig decomposed stdlib control | PASS, 4.736 seconds, 13 synthetic completion requests |
| Actual rig decomposed packaged API control | PASS, 19.360 seconds, 13 synthetic completion requests |

## Actual vertical control and carry-forward

The two real rig controls bind source `8d43977`, harness `162819c48a3449e00add6b7fb2232c11b6dff1a2c2188a5413fb8263ace135d9`, fixture manifest `9d6b6dc798d148524ef7e360abfc31958a47bb05b6870e56735a7ef64c283e5b`. The successor diff adds only the result-publication cancellation/deadline fence and its caller. `arm_work`, environment binding, Factory, checks, checkpoint and mode restoration are unchanged; these results carry forward without repeating Docker controls.

Both executions used real `arm_work`, BudgetWorker debits, Factory, generated-test/acceptance verification, real offline prepared Docker profiles, real Git checkpoint and mode restoration. Both children and final acceptance passed. Post-cleanup integrity was true and all four workspace-owned container labels were confirmed absent. All five request roles appeared in each 13-call ledger. Source/reference files were injected through synthetic run-tool replies inside the real worker container.

Patched seams were exclusively the BudgetWorker constructor's mandatory networkless transport and controller socket denial. Dummy identity config contained no key. The fake worker public endpoint was `http://127.0.0.1:1`; no real model transport was constructed. Private reference bytes exist only in this separate synthetic proof tree, never actual pilot arms. Serving readback remained container `2cac4229…`, image `249ed60f…`, start `2026-10-04T14:20:09.194925789Z`, running. First readback was during the short control, final readback afterward; no earlier independent baseline is claimed.

Full private evidence: rig `/home/gradrix/gflo-planning-harness-controls-v1/results`. Compact results, final verifications, restoration receipts, ledgers and readback are in `qa-harness/`. Commands: `python3 ops/test_planning_pilot_qa.py`; synthetic rig invocation `python3 ops/planning_pilot_vertical_qa.py --bindings environment-bindings.json --output results` from the isolated staging directory.

## Supplemental evidence and boundaries

Builder actual SIGTERM/descendant controls are in `builder-controls.txt` and `ops/test_planning_pilot_builder.py`; these are supplemental, not independent QA executions. Separate security review reports 18 controls passed, including actual SIGTERM/deadline during publication fsync. The original publication race is preserved against the predecessor; its repair is assessed by that separate review. No claim of actual-model planning performance, live cancellation of inference, or semantic superiority follows from synthetic controls.

Independent test SHA256: `1ff0479a52c567d8d98f4cd19be33973798b29baeb933b6ab3705bdc7cfb1971`. Synthetic driver SHA256: `e17e9924fddd94f8ae4d85e3fb7b2813d84a0f8ad9989f8c72315c28c3a735d6`. Both are final/stable. Initial independent probe setup errors (non-loopback dummy endpoint, then absent sandbox observer) were corrected in the probe; they were not product defects.

## Combined-suite probe isolation correction

The first combined suite exposed an independent-test isolation bug: direct `arm_work` invocation left its intended Git environment sanitization in the test process. The controlled test now restores the complete original environment with `patch.dict`; all eight independent checks pass again. Product code and actual vertical evidence are unchanged. The original combined failure remains in `combined-controls.txt`; final combined rerun belongs to the coordinator.
