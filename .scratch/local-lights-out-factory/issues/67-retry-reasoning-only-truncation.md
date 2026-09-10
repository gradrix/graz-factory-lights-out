# Retry reasoning-only output truncation within existing budgets

Type: task
Status: resolved
Blocked by: 66

## Evidence

Frozen window-reasoning-v1 feature-2/3-reasoning test workers returned HTTP success
with finish_reason=length, content=null, and all 6144 completion tokens consumed by
reasoning. The decoder rejects null content before its existing truncation branch,
classifying a bounded model-output failure as an infrastructure/protocol halt.

## Scope

For the new reasoning window profile, route a valid, accounted length response with
null content through the existing retryable truncation path. Never apply partial text
or reasoning, accept malformed accounting, permit tool/refusal responses, increase
budgets, or alter historical profile semantics. Keep the frozen issue-66 results.
Test null versus partial content, finished null responses, accounting rejection and
finite retry behavior. Qualify fresh repair work on the retained failing input with
unchanged model, requirements and gates; preserve every spent response.

## Answer

The new reasoning-window profile now recognizes accounted null-content length
responses as bounded truncation, preserving all other protocol checks and historical
profiles. Unit regressions cover null/partial output, finished null rejection, invalid
accounting, evidence retention and existing finite retries.

Two fresh unchanged-plan follow-ups exercised three truncations without protocol
halts or partial application. Both implementations accepted, neither full feature did:
one test worker exhausted retries on invented helper signatures; the other on another
truncation. 13 responses / 109,344 tokens / 593.50 model seconds, within reservations.
[All results](../window-reasoning/README.md). 515 tests/25 subtests, lint/typing and four
historical replays pass. Issue 68 investigates definition grounding; no default upgrade.
