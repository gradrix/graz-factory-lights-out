# Improve bounded validation feedback

Type: task
Status: resolved
Blocked by: 18

## Evidence

The frozen held-out campaign's first balanced-brackets run exhausted ten attempts
with the same string/object input mistake. Each candidate was independently rejected.
Retry context embeds stderr as base64 in a large raw Execution JSON; this may obscure
the actionable traceback and input shape. This is a hypothesis, not a demonstrated
cause of the model's failure. Inspect retained views and compare a separate diagnostic
follow-up after the frozen campaign completes.

## Scope

Keep raw execution artifacts immutable. Compose bounded decoded stdout/stderr and
command/input details for worker feedback, preserving evidence hashes and treating
all content as untrusted data. Cover invalid UTF-8, output limits, terminal control
characters and multiple gate cases. Do not modify policy during scored repetitions.
Version any changed context policy prospectively; previously scored tasks become
regression fixtures, never fresh held-out successes.

## Acceptance

A focused regression test demonstrates meaningful readable feedback with retained
provenance. Real local-model follow-up compares the failed task under the changed
policy and reports all attempts without rewriting the original campaign score.

## Answer

Implemented `gflo.feedback.validation_feedback` and context policy bounded-python-v4.
Raw provenance and private expected outputs are preserved. Nine projection tests cover
later-case selection, malformed bytes, controls and bounds. A matched seen-failure
follow-up repaired 3/3 seeded bracket failures with readable feedback versus 1/3 with
legacy feedback; actual model calls were 3 versus 6. No held-out rescore. Evidence:
`.gflo/evidence/feedback-recovery-v1/`. Semantic version repair still fails, so readable
feedback is useful but insufficient for every failure. [Campaign report](../heldout-results.md).
