# Disposable two-task local planning comparison

Agent-defined experiment under the user's authorized incremental local-factory work. Baseline maintained runtime92deaab, accepted/published atc81429b. No maintained runtime mutation or installation in this unit.

## Decision and isolation

Compare one direct Factory assignment with a local-model plan followed by exactly two ordered Factory assignments. Use two fresh realistic multi-file increments: one Python stdlib CLI/data task, one packaged Python API task. Independent fixture author selects concrete domains after checking prior cases, freezes complete policies/interfaces/public criteria, milestone and full acceptance, and demonstrates starter failures/reference passes in the exact approved environments. Model-visible source is a clean small Git repository, within existing review limits. Oracle/reference source stays outside every model/worker mount and prompt.

Quarantine code/fixtures in branch prototype/planning-pilot-20261004 and its separate worktree. Do not edit gflo/, maintained tests, runtime configuration or serving profile. Main keeps this contract, coordination, compact evidence and outcome/branch pointer. Prototype cannot silently become production code.

## Four bounded arms

Order: caseA direct, caseA decomposed, caseB decomposed, caseB direct. Same frozen initial source, public requirements/milestones, final acceptance, prepared environment, model96K/Q4/one slot, medium reasoning and per-call4096output/1024thinking cap. No cloud fallback. Each arm has **48 total completion requests and1800seconds work**, including planning, review, implementation, tools, verification and handoff. All HTTP completion attempts debit before transport, including failed/malformed calls and question assessment; child tasks cannot replenish credit. Record actual server usage without inventing an aggregate token ceiling or missing usage. At most3attempts/24workerturns per child within the shared pool. Per-request timeout is shortened to remaining time; an independent outer supervisor enforces the wall deadline. Identical bounded cleanup allowance of150seconds follows; never publish parent success after work deadline/cancellation.

Use the existing ModelWorker.request seam for every model completion. Planner makes one proposal; a fresh-context plan reviewer makes one review. Deterministic schema/requirement coverage/dependency checks and the review must pass before dispatch. No uncharged human plan rewrite or automatic replanning in this pilot. Invalid/unsupported plans fail the arm explicitly. Plan output cannot choose checks, packages, environment, budgets or permissions. Original accepted requirements remain authoritative in both task contexts.

Task1 uses fixed independent milestone checks. Verify its accepted candidate/patch/contract/environment identities, then copy its complete workspace into a fresh private Git checkpoint with verified paths/types/modes/content. Do not mutate the accepted workspace or original source. Task2 starts at that exact checkpoint; reject changed inputs. The full increment acceptance and fresh code review determine final outcome, identical to direct. Intermediate acceptance is not final acceptance. No merge/rebase/parent resume/deployment claim.

Every state change writes bounded inspectable progress and charged-request evidence outside worker mounts. Preserve raw model requests/responses, plans/reviews, child run IDs, patches, checks and all failures with hashes. Do not expose credentials or complete private configs. Original repositories and prior accepted candidates stay unchanged. Existing child progress tools may be reused; a simple prototype status command/journal is sufficient.

Cancellation/deadline stops dispatch, terminates the owned controller/client and cleans owned executors. Killing a client does not prove the model slot idle: obtain positive serving-idle evidence before another arm, or stop with an explicit unresolved condition. Never restart or alter shared services as a hidden recovery. No inference until this serving-lifecycle route is established. An interrupted arm remains failed/interrupted; retry requires a new labeled experiment/output, never an implicit reset.

## Gates and interpretation

Before real calls, independently review harness boundaries and prove with controlled clients/disposable repos: every role charged; denial before an extra request; failed transport/child restart cannot regain credit; actual outer deadline/cancel terminates owned work without accepted parent result; changed checkpoint/patch refuses; task1-pass/task2-or-final-check-fail remains increment failure; original/prior-good state unchanged. Exercise slot-idle classification and refusal of uncertainty without disturbing unrelated services. Fixture starter/reference controls must run in the exact prepared profiles, with offline execution and explicit runtime/image/dependency identity.

Freeze harness/fixtures/baseline/serving identity and all budgets before four model arms. One attempt per arm under the above internal repair limits; do not edit tests after exposure or quietly repeat failures. Independent final review covers all requested behavior, preservation, generated tests/docs, candidate integrity and unjustified complexity. Record false acceptance, complete outcomes, interventions, calls/usage and elapsed work/cleanup. All failures and zero-benefit outcomes remain evidence.

This two-case pilot can identify a useful route or a concrete failure. It cannot establish a reliability rate, statistically demonstrate superiority, qualify Stage5, or authorize automatic integration into original projects. If decomposition adds no value, retain it as advisory and choose the next smallest evidenced improvement.
