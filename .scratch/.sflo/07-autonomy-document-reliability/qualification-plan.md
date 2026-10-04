# Two-phase qualification preparation

Prepared harness: `qualify-documents.py`, SHA256 `6358feb74d26f966efd38ec91f083f16fb288aeee859f6d75ab90fbca6abf7f0`. Syntax checked only; no source acquisition/model/container calls. Candidate source is still awaiting its final frozen handoff. All source/runtime adaptation must be reviewed against that handoff before execution.

## Phase1: acquire and freeze, no inference

Root stages the candidate, frozen qualification directory `.scratch/autonomy/document-repair-qualification`, and harness. Use a fresh output path. `acquire` calls the candidate's public `DocumentStore.acquire` for all three approved official3.12 URLs, resolves complete evidence/spans, saves source IDs/body hashes/times and comparison to the preserved cached baseline. Every fetch uses the candidate's actual40K extractor; this does not substitute old cached records for the acquisition gate. Errors persist as `not_attempted_source_failure`; no model calls occur, and answer phase cannot proceed unless all three succeed.

Common arguments:

```sh
python3 QUALIFY_SCRIPT acquire \
  --repo FROZEN_REPO --candidate FROZEN_MANIFEST --candidate-sha256 FROZEN_HASH \
  --qualification FROZEN_QUESTION_DIRECTORY \
  --qualification-manifest-sha256 0fd8ecff10b17c584e049ae072eb9f31c67f6c33f4dc70beebfbc457e1394de1 \
  --serving-container gflo-model --expected-serving-id EXACT_ID \
  --expected-serving-image EXACT_IMAGE --output FRESH_OUTPUT --run
```

The serving inspection records only ID/image/alias/context/KV/parallel, accepts long and short flag spellings, and validates96K/Q4/one slot. It never emits complete argv, environment, key path or private config. Candidate/qualification hashes are checked before and after phases and each case.

## Independent source-alignment gate

Before any answer call, independently read all three newly acquired sources against every frozen expected fact, including unsupported premises. Compare new extraction and dates with the cached baseline. A matching body is helpful but does not skip alignment review. Changed bytes are neither an automatic failure nor authorization to silently rewrite facts. Preserve original contract/oracle/baselines and add a source-specific explanation identifying changed body/version and why all requested facts still align. If an expectation no longer aligns, stop and freeze a separately justified cohort revision before inference.

Save an explicit reviewed gate JSON; root's coordinator go is workflow authorization, not a new user approval request:

```json
{
  "binding_sha256": "SHA256_OF_ACTUAL_OUTPUT_BINDING_JSON",
  "qualification_manifest_sha256": "0fd8ecff10b17c584e049ae072eb9f31c67f6c33f4dc70beebfbc457e1394de1",
  "decision": "aligned_for_inference",
  "reviewer": "independent reviewer identity",
  "coordinator_go": true,
  "cases": {"EACH_OF_TEN_CASE_NAMES": "aligned"},
  "changed_source_addenda": {"EACH_CHANGED_SOURCE": "Explicit body/version comparison and factual alignment notes"}
}
```

This is a schema illustration, not an approval. Harness requires exactly the ten case names and a nonempty addendum for every changed source. Gate itself is SHA-bound at invocation. Source questions retain historical-series wording: acquiring a page today does not make its3.12 content current-runtime guidance or exact-patch documentation.

## Phase2: one public answer invocation per question

Run the same common arguments with `answer`, adding `--config PRIVATE_EXISTING_CONFIG --gate REVIEWED_GATE --gate-sha256 EXACT_GATE_HASH --run`. Existing acquisition output is required. An existing `answers` directory is refused, including partial failures: there is no external retry or resume-to-hide-failures. Root can preserve and assess partial outcomes before deciding any new trial.

Only questions and source evidence enter the request; oracle expected facts and reference span IDs never enter messages. Each case calls `store.answer` exactly once. Product code owns its maximum two internal calls and structural-only repair rule. Harness uses ordinary ModelWorker, with no fork-local capture counter. Product immutable `response-1.json`/`response-2.json` and attempt ledger are authoritative; complete public initial requests and rendered answer/diagnostic receipts are saved for review. Failed diagnostic IDs remain failures. Never infer semantic success from valid provenance.

Afterward, independently review all ten final answers and all original/repair attempts. Then perform the contract's separate actual network-none replay with frozen sourceRO/storeRW, no model config/keys/client, and unchanged record hashes; existing root replay pattern is reusable. The two-phase script does not claim that last gate itself. Cached baseline identities, prior four unattempted asyncio outcomes, and all earlier failures stay untouched.
