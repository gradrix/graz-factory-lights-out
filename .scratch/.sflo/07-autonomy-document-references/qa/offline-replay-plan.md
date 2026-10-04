# Prepared actual rig cross-version replay

`offline-replay.py` SHA256 `7976002b8ed2f3b6a3733ae14fe3fb0971d86f3b405933253f81dff793530ae4`. Syntax checked only; no execution. Candidate adapter validation awaits frozen source; invocation additionally refuses until the new13-case summary is complete.

```sh
python3 offline-replay.py \
  --repo NEW_FROZEN_REPO --candidate NEW_MANIFEST --candidate-sha256 NEW_HASH \
  --trial COMPLETED_NEW_TRIAL \
  --format2-trial /home/gradrix/gflo-documents-2fe870d/.gflo/qualification-1 \
  --format2-summary-sha256 REVIEWED_EXACT_TRIAL1_SUMMARY_HASH \
  --legacy-trial /home/gradrix/gflo-stage4-9c01da1/.gflo/trial-1 \
  --legacy-receipt-sha256 REVIEWED_EXACT_LEGACY_RECEIPT_HASH \
  --output FRESH_PRIVATE_REPLAY_OUTPUT --run
```

The candidate path/hash is explicit, not hardcoded to2fe870d. The two historical trial paths above identify the preserved actual runs and may be supplied explicitly elsewhere with the same reviewed record identities. Legacy answer IDs are pinned. New summary/binding/candidate identities and old summary/receipt hashes are checked. Require exactly13new+10oldformat2+2legacy cases; retain both old diagnostic failures and any new diagnostic failures, never fabricate answer outputs.

Privately copies all three stores with original modes. Executes one pinnedPython3.12 ordinaryrunc/networknone/nonroot/readonly container, with frozen sourceRO, trusted script/case filesRO and three privatecopiedstoresRW. No model config, keys, socket or other project mounts. Saved inspection proves actual image/network/runtime/mount set. Thirty-second replay wall cap and bounded cleanup; no model/network calls in child. Original and copied regular record-file hashes must stay identical, excluding only each root `.lock`; original stores are never mounted.

All successes must replay identically except age_seconds and retain their exact format1/2/3. Diagnostics must resolve and refuse replay with unchanged failure semantics. Result/inspection/cleanup/rawstdout/stderr remain in output. Candidate files rechecked afterward. This is a prepared evidence plan, not a replay or acceptance result.
