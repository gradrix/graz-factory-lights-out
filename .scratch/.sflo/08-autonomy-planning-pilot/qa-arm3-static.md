# Arm 3 static failure forensics

**Failed arm preserved; no rescoring.** API decomposed arm took 873.540 seconds and exhausted all 48 shared completion requests: 45 implementation, one code review, planner and plan review. Child1 `ba6255bd4d74` accepted its milestone; child2 `300151e5e413` did not complete. `child-result.json` records `RuntimeError: Shared completion request budget exhausted`. Ledger ends at returned request48; no49th capture. Historical cleanup/idle confirmation remains distinct from product correctness.

Evidence root `.gflo/planning-trial-1/3-config-preview-decomposed`. Independently hashed retained child2 names/modes/bytes: `93275b3e323ea486cdb544c6126fe98883ee184f15f1bf8c9c27a12af6479c9c`. This is a failed retained workspace, not an accepted candidate. No candidate execution, Docker or model calls during review.

## Concrete unresolved defects

1. **B4 HTTP body is not bound.** In retained `src/config_preview/routes.py`, `preview_endpoint(payload)` lacks `Body(...)` or another body-binding annotation. Its implementation expects a dictionary JSON body. The final actual installed-package test commands (requests47/48; child2 trajectory turns20/21) ran15tests and failed two: success got422 rather than200; conflict got422 rather than409. Static cause agrees with recorded results: unannotated payload is interpreted as a required query parameter. Domain code is never reached for ordinary JSON-only calls. No subsequent repair was dispatched.
2. **B1/B2 scalar-depth limit is incomplete.** `validation.valid_document` checks the depth only at object recursion, while scalar children merely increment node count. `domain._depth` likewise recurses only into dictionaries. A chain with root depth0, dictionaries through depth6 and scalar child at depth7 is accepted by these predicates, contrary to the public rule that every child increases depth and maximum is6. The analogous post-insert bound can miss scalar depth7. This is static reasoning pending the coordinator's already planned offline depth probes; do not label it a measured failure yet.

## Repair trajectory and budget use

- Requests1–2 planned/reviewed B1/B2 first, remaining requirements second; complete public requirements were retained.
- First child spent requests3–26 implementing validation/domain/audit and debugging value/node counting, then request27 received a pass review. Its saved milestone success does not establish omitted full-case boundaries.
- Child2 began at request28. It implemented routes (33), meaningful HTTP tests (34), and README (35).
- Request36's build/install+discovery command reported zero tests. Requests37–44 explored a nonexistent `unittest.discovery` module, invalid exploratory syntax, then actual loader source. Request45 added `tests/__init__.py`.
- Request46 exposed missing installed package in a later tool call. Request47 explicitly recognized temporary directories do not persist between calls and combined build/install/test. This reached15 real tests, two failing HTTP cases. Request48 retrieved the full failures. The next completion was denied by the shared ledger before dispatch.

This supports a concrete account of time/credit spent on test discovery and ephemeral installation state, not a claim that decomposition alone caused failure. The model eventually obtained actionable HTTP failure evidence but had no remaining request to repair it. Pipeline tail commands returned shell0 despite displayed test failures; captured test output itself was visibly failing. The controller did not falsely promote the arm.

## Other semantic/test/docs observations

Type-strict recursive equality, copied audit snapshots, nonmutation, absent-versus-null representation, prevalidation before conflicts and node counting appear coherent on inspection. Fifteen generated test methods are substantive, including HTTP success/conflict checks that genuinely caught the route defect. Depth tests require independent verification against the scalar-node interpretation above.

README explains the required behavior and includes a logically consistent HTTP request/response example, but the retained HTTP implementation cannot produce that example. Its offline wheel/install instructions and plain `uvicorn` entrypoint have not been independently executed; exact approved-profile command availability should be checked later. No new lexical documentation rule is imposed. Code is longer than the reference but no separate consequential filler finding is needed.

Deferred dynamic scope: builder's frozen API probe for scalar depth6/7, resulting-depth limits, strict equality/aliasing and installed HTTP/tests; README commands in the approved offline profile. Any later pass would describe retained code only and would not reverse this failed arm or its consumed48-call result. No fixes or feedback to the timed model.
