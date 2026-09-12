# Varied complete Python projects

Two new stdlib projects: csvfold aggregates strict CSV inventory quantities;
dagorder computes deterministic dependency ordering from JSON. Each model builds
an API, CLI, installable package, tests and README from a brief plus untouched
archive sentinel. Two trials per project are frozen before inference using the
same pinned deployment, non-reasoning windows profile and Taskdock project budgets:
36 responses / 565,248 tokens maximum per build; 2,260,992 tokens reserved overall.

Codex authors specs, independent checks and trusted reference implementations to
qualify the checks. References never enter planner/worker inputs. Five independent
gates check API, real CLI processes and direct main calls, offline installation,
documentation, and generated tests rejecting three behavior mutants. Checks include
raw input boundaries, integer formats, duplicate JSON keys/prerequisites and exact
ordering. Failures include observed and expected results. Separate post-acceptance
checks use randomized CSV aggregation or permuted DAG encodings and adversarial
inputs. All twelve reference preflights pass, with bound gate/evidence digests in
preflight.json and raw receipts under `.gflo/evidence/varied-projects-preflight-v1/`.

Reproduce from the factory root with the pinned model and broker available:

```sh
.venv/bin/python .scratch/local-lights-out-factory/varied-projects/campaign.py --preflight
.venv/bin/python .scratch/local-lights-out-factory/varied-projects/campaign.py
.venv/bin/python .scratch/local-lights-out-factory/varied-projects/report.py
```

Campaign/preflight refuse existing roots. Preserve terminal failures and replay
without further inference; don't reset attempts or fix generated plans/source.
Only independently audited acceptances are exported as exact files in deliveries/.
These new supervised projects broaden the domain sample; they do not substitute for
varied real legacy repositories or qualify arbitrary external dependencies.

## Outcomes and review

All four builds are terminal: CSV 0/2 complete (repeated test/documentation output
truncation); DAG 1/2 historically accepted (other build returned README outside the
required JSON changes field). The accepted DAG passed the initial randomized audit.
Source review then found further required-input defects missed by the frozen checks:
non-strict CSV parsing accepts malformed quotes; DAG regex matching accepts a
trailing newline; the accepted DAG CLI leaks a traceback on invalid UTF-8.
Independent post-review checks pass references and fail all four accepted core
candidates plus the one combined acceptance. Exact acceptance findings now block
reuse without rewriting historical results or adding replay events. Generated DAG
files are preserved byte-for-byte under challenged/dagorder-2, not deliveries.
There are **zero fully qualified original projects out of four**.

The four builds used 44 responses, 188,725 tokens and 783.21 model seconds.
All 44 tokenizer/generation messages and output reservations pass the wire audit;
maximum prompt 5,399 tokens. Every terminal replay is unchanged, with challenged
reuse blocked. No model plans, candidate source or tests were manually fixed. New
post-review checks never entered these frozen worker requests. This exposes both
model reliability and supervisor-authored gate coverage limits. The test-count gate
counts test functions; future briefs/checks should explicitly distinguish function
count from parameterized collected cases to avoid an unnecessary implementation
constraint (it did not cause these protocol/output-limit halts).

Next work needs compact valid response generation, stronger boundary-driven checks,
and fresh trials. Do not promote a default profile or claim unattended delivery.
These trials also do not qualify large execution or external dependency provisioning.
