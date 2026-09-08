# Bounded local model turns

`compose_view` and `LocalModel.turn` implement the first Python worker profile. They produce a validated edit proposal or a permitted `read_file` request. They never modify source files, invoke a tool, grant authority or accept work. The controller must hold a valid Lease and enforce transitions when it connects these calls into the durable loop.

Inputs are a self-contained, immutable `SourceBundle` and a prepared `WorkAtom`. The atom's `inputs_digest` must equal the canonical digest of `InputSnapshot(source_digest=..., source_revision=...)`. Source, deployment and diagnostic artifacts must exist and verify. The caller supplies a `current_inputs` callback; the client checks it before composition, before generation and after receiving the response. That callback must observe the controller's authoritative snapshot. It is not an automatic working-tree watcher.

The profile currently supports `python-pilot-v1`, `none-v1` network/credential profiles, `pilot-v1` sandbox, and the `read`/`edit` grants. Cross-bundle dependencies and upstream-contract retrieval are rejected rather than silently omitted. The worker receives the objective, non-goals, requirement IDs, path/tool grants, concise environment, selected source text and at most four explicit diagnostic projections. It does not receive gate expectations or validator plans. Do not supply raw gate reports as model diagnostics: create a `Diagnostic` containing the intended observation and the digest of its retained source evidence.

Every visible existing writable file is required context. Optional supporting files can be omitted explicitly and requested later. The view records per-file content hashes, selection reasons, source-data authority, omissions/reasons and diagnostic provenance. Source/diagnostic text is marked as untrusted data; deterministic checks enforce the actual authority boundary. This is a bounded bundle projection, not a general Product-graph context composer or calibrated retrieval policy.

`LocalModel` accepts an explicit numeric-loopback HTTP `/v1` endpoint and a `ModelProfile` with a retained deployment-config digest. It does not read proxy settings, follow redirects, resolve remote hosts, use credentials or fall back to a cloud provider. The profile supports the verified vLLM API, including `/tokenize`; SGLang worker-client compatibility is not claimed. The deployment digest is configured provenance, not remote attestation of model weights. The smoke script separately checks the running container's pinned image and checkpoint/tokenizer revision flags.

Calls serialize per endpoint across this user's clients through a file lock. One wall-clock deadline covers lock acquisition, model listing, tokenization and generation. HTTP capture is capped at 2 MiB and rejects incomplete/ambiguous JSON. There is no automatic retry. A client timeout closes transport but does not independently certify when the server has stopped computing; controller recovery must account for this before retrying.

The client tokenizes the exact chat messages and thinking-disabled template through the same server before generation, requires the expected served context limit, and reserves the atom's output tokens. Overflow is rejected before generation. The completion must name the expected model, contain one stopped assistant choice, and report token usage matching the preflight count and reserved budget. Truncation, native tool calls, refusal, malformed JSON, duplicate keys, unknown result kinds, extra authority fields, unsupported paths/tools and invalid file contents are rejected. JSON mode helps formatting; it is not treated as sufficient schema validation.

An edit result contains complete replacement text for granted paths. It cannot delete files, modify prohibited paths or replace unrelated files. `candidate_bundle` merges an already validated proposal with its pinned source; the controller publishes it before submitting it to the ledger. A `read_file` result is only a typed request into the immutable source bundle; it does not authorize host filesystem access. The [durable controller](controller.md) now connects bounded tool-response turns, retries and interruption/resume for one prepared task. Product-graph scheduling remains pending.

The artifact store retains the view, token/context manifest, profile, outgoing requests, raw responses, typed turn or error, token usage and elapsed time. Nested provenance references are retained under the existing no-GC policy. A model error leaves diagnostic evidence; a caller can inspect `last_evidence_digest` after the turn. Model observations do not become trusted gate evidence merely because they are stored.

## Local coding smoke

Run with the installed development environment and existing qualified vLLM service:

```sh
.venv/bin/python scripts/check_worker.py --output .gflo/evidence/worker-new-run
```

Choose a new output directory. This sends only a fixed synthetic repair fixture, not repository content. It asks the model to fix first-occurrence deduplication, validates the proposal, qualifies the broker, confirms the original program fails an example, and tests the generated candidate against three controller-owned cases in fresh containers. A passing gate can then produce durable acceptance. The script deliberately has no retry/resume loop; it is not the twelve-task pilot.

The final smoke passed with 626 prompt tokens and 75 completion tokens; the whole client turn took about 7.15 seconds. This includes local request/tokenization work and is not a sustained decode benchmark. Both smoke runs passed the three cases. The [verification record](../.scratch/local-lights-out-factory/worker-verification-results.json) pins raw local evidence and source hashes. The focused worker/client suite has 34 passing tests. The full default suite has 147 passing tests and 23 passing subtests; eight optional broker tests skip without their explicit environment variables and were separately qualified in the preceding broker slice.
