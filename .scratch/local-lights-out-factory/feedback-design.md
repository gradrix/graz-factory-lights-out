# Readable validation feedback — prospective change

Observed held-out failure: bracket task assumes a dictionary input, despite the
string requirement. Ten attempts repeat the same exception. Retry diagnostics
contain encoded stderr. Keep this result failed; it supplies a development fixture
for the next policy version.

Add one `validation_feedback(observation) -> str` projection at the controller's
existing diagnostic boundary. Preserve the current raw observation artifact and
Diagnostic.source_digest. Present gate/outcome, final executed case index, command,
input, exit status and decoded stdout/stderr. A gate stops on the first nonpass,
so the final execution is the actionable one; earlier cases remain in raw evidence.
Do not include expected outputs or trusted gate implementation in the Worker view.

Use strict base64 decoding, visible replacement for invalid UTF-8, escaped control
characters and explicit truncation markers. Bound individual fields and the total
8,192-character Diagnostic budget. Malformed/inconclusive execution data must still
produce a readable failure description without masking the original failure.

Validate that a later failing case survives projection; test oversized stderr,
invalid base64/UTF-8 and terminal controls. Existing scope and input-freshness checks
continue to decide authority. Bump context policy prospectively, then run the failed
bracket task separately without updating any original score or describing the task
as unseen. Record all follow-up costs and whether decoded feedback actually helps.
