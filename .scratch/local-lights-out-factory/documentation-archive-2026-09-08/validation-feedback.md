# Bounded repair feedback

Context policy `bounded-python-v4` replaces encoded execution JSON in retry feedback
with a bounded readable projection. It shows the gate and outcome, last executed case,
command, input, exit status and observed stdout/stderr. The gate stops on a nonpass,
so the final execution is the actionable case; earlier cases remain in raw evidence.

The Diagnostic still references the immutable raw observation. Expected outputs and
trusted gate implementation are excluded from worker feedback. Invalid base64 and
UTF-8 are reported visibly, control characters are escaped, and truncation is explicit.
Per-field limits keep the projection within the 8,192-character Diagnostic bound;
the exact tokenizer/context budget still applies to the whole Worker view.

This improves access to observed failure information. It does not guarantee successful
repair or compensate for an underspecified product input/output contract. Evaluation
under an older frozen policy remains unchanged. Seen failures used for follow-up are
regression fixtures, not new held-out successes.
