# Independent browser qualification driver

Prepared, not executed against moving source. `.scratch/autonomy/qualify-browser.py` SHA256 `9116e083def1f6e93b394d84fe0b5c8855e6ee497a89d14c17429e4c3dc61b4d`; syntax compilation/help passed. Final candidate handoff is required before `--run`.

```sh
python3 .scratch/autonomy/qualify-browser.py \
  --repo /absolute/frozen-checkout \
  --candidate /absolute/final-candidate.json \
  --candidate-sha256 FINAL_CANDIDATE_SHA256 \
  --fixture /absolute/evaluations/local-browser \
  --fixture-sha256 20d07c59c1af28f5728847179406560787b579b86c20c030e30032492f16ac10 \
  --support-store /absolute/prepared-browser-store \
  --support-id EXACT_SUPPORT_ID \
  --output /absolute/new-independent-trial \
  --run
```

No support downloads or model calls. Driver refuses existing output, verifies frozen source/fixture hashes, resolves existing support, copies it preserving modes into a new private store, and checks support identities before/after. It runs five known-good journeys then one focused app mutant per journey. Every request, mutated input, complete receipt, unexpected failure and bounded trace audit is retained. Expected mutant outcome requires journey-phase failure and confirmed cleanup, not an unrelated startup/artifact error.

For validation, the browser mutant changes stock on an overstock409; the previously frozen HTTP-only422 mutant would be intercepted by frontend validation and is unsuitable as the actual browser negative. Other mutations remove a created record, subtract the full edited quantity, permit overbooking, or mutate before503. Original HTTP preflight evidence remains unchanged.

Positive controls require screenshot and opaque trace bundle, one context for ordinary cases and two for conflict. Independent QA reads bounded ZIP members in memory only, never extracts to the host or renders trace content. It checks outer manifest hashes/sizes against inner trace bytes and runtime trace manifest, then confirms second-context recorded fill value `Second` and Reserve click (actual recorded actions, not page prose). Aggregate trace16MiB stays unchanged. This addresses the repaired scope without erasing the original primary-only trace gap.

Driver success means fixture controls passed, not complete browser/security/rig acceptance. Lifecycle, denial controls, resource/isolation observations and final gate remain separately required. Original trace-gap finding and original candidate verdict remain preserved.
