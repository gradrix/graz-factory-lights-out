# Per-requirement review units

Decision: user, 2026-10-07 — "go with a recommendation. And let's make this as autonomous as possible - and able to be scalable." Recommendation taken: per-requirement finalization (option1) with fail-closed thinking exhaustion (option3). Design below is agent-authored under that direction. Predecessor ../09-autonomy-review-evidence/run.md (contract3f7f503d…, prototype c3673ba): 3/4, case04 false acceptance after every fresh request exhausted the 1024-token thinking budget. Its evidence is immutable; no rescore.

## Question

Does splitting one whole-objective diagnosis into one request per objective requirement keep reasoning inside the frozen profile and return the four expected classifications with grounded findings? Same saved-evidence inputs (package manifest 303f7026…), same known cases, no candidate execution.

## Units (generic, autonomous)

Units are derived mechanically from the public objective: one unit per nonblank physical objective line, in line order. No human or fixture-specific splitting. At most32 units per case; overflow is an explicit capacity failure. A unit's request is: the unchanged system policy plus a unit rule, the case's identical numbered evidence view (objective lines, numbered source, catalog), then a final short assignment naming the unit's line number and text. Identical prefixes across a case's units allow serving prompt-cache reuse; recorded `timings.cache_n` measures it.

Each unit uses its own unchanged durable `CaseLedger` in final phase: exactly one precharged JSON-only completion, no tools, no retry. Per-unit work150s, HTTP≤120s; case work = units×150s; cleanup150s. Frozen flash-next-coder 98304 context/Q4/one slot/medium/temperature0/4096 output/1024 thinking.

## Unit wire

The predecessor versioned validator, plus: every finding's `requirements` includes the assigned line. Decision is about the assigned requirement only; findings for other requirements are rejected.

## Fail-closed exhaustion

After each returned completion, one non-generative metering call (`/tokenize` of `reasoning_content`) counts reasoning tokens. Calibrated on the predecessor: all four truncated responses measured exactly1024. Count ≥1024 marks the unit `exhausted`: incomplete, never admissible pass. Metering failure is also incomplete.

## Aggregation

Case incomplete if any unit is incomplete, failed, exhausted or invalid. Otherwise repair if any unit repairs; else needs_input if any unit asks; else pass. The report keeps every unit's findings with its unit line; no model-authored aggregate.

## Gates and acceptance

Offline controls: unit derivation (blank lines skipped, cap), assignment validation, exhaustion classification from recorded predecessor numbers, aggregation truth table, one completion per unit via unchanged ledger, metering failure fails closed, prefix identity across units. Then the four-case trial on the5090 through a repeatable driver.

Acceptance: 4/4 expected classifications from complete units only (no exhaustion), every blocking finding grounded in actual captured evidence, no unexecuted-test/verified-fix/unsupported-requirement claims, unchanged packages and cleanup/idle. Automated scoring against private expectations covers classification and completeness; grounding is separately assessed. A pass permits a fresh-case qualification decision only; no maintained promotion.

## Scalability record

Measure per-unit latency, cache reuse, reasoning tokens and total case time, so cost per requirement and the benefit of more serving slots can be projected rather than assumed.
