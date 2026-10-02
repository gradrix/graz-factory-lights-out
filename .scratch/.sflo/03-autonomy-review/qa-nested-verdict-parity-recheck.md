# Nested-verdict delimiter parity recheck — PASS

Frozen candidate `b0342ccfbe47d6f345dc10a540ceaf96386eabf4`. Scope: the prior conservative over-redaction boundary and original nested-value privacy regression. No maintained edits, target models, GPU, rig or executor changes.

- All original **30 worker/HTTP cases** pass: full synthetic values absent, recorded JSON valid, ordinary fields/types retained, exact prior verdict still reaches the model, private artifact bytes unchanged.
- **15 delimiter controls** pass: zero/two/four trailing backslashes across raw plus one through four JSON encodings hide the credential and preserve following `ordinary=KEEP` text.
- **Five discriminating escaped-quote cases** pass: an internal escaped quote followed by `BETA` does not terminate redaction early; both secret fragments disappear while the following ordinary text survives.
- **13 observation + 8 worker regressions** pass on this candidate.

Both previously observed privacy and trailing-evidence preservation findings are closed within tested representations. No claim of universal credential-format detection or rerun of the unrelated full suite.

Reproduce: `python3 .scratch/.sflo/03-autonomy-review/qa-nested-verdict-parity-probe.py` (exit 0). Complete saved probe/log/JSON share that basename. Focused test evidence: `qa-parity-observer.log`, `qa-parity-worker.log`; tests imported source reconstructed by `qa_pinned.py b0342ccfbe47d6f345dc10a540ceaf96386eabf4`. Prior frozen failing evidence remains intact.
