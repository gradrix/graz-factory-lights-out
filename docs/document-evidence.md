# Approved historical document evidence

The `documents` CLI acquires one controller-approved public HTTPS page, extracts inert text offline, and stores a historical snapshot. It does not search, browse, crawl, or give the model network or tool authority. Package preparation retains its separate allowlists and lock checks.

Create an approval JSON file:

```json
{
  "url": "https://docs.python.org/3.12/library/json.html",
  "source_version": "Python 3.12 documentation snapshot; floating series, not an exact runtime patch guarantee",
  "question": "Which separators remove separator whitespace?"
}
```

An optional `expected_sha256` pins the raw response body. Approval is for the exact URL: queries, fragments, credentials, non-443 ports, ambiguous characters, redirects, nonpublic DNS answers, and unsupported response encodings are rejected. The client resolves once, connects to a checked public IPv4 address, and verifies TLS for the original hostname. It sends no cookies or authorization. Restrictive or ambiguous retention headers prevent acquisition.

```sh
python3 -m gflo documents --store .gflo/documents acquire approval.json
python3 -m gflo documents --store .gflo/documents inspect EVIDENCE_SHA256
python3 -m gflo --config config.json documents --store .gflo/documents answer EVIDENCE_SHA256
python3 -m gflo --config config.json documents --store .gflo/documents answer EVIDENCE_SHA256 --question 'What is the future release date?'
python3 -m gflo documents --store .gflo/documents replay ANSWER_SHA256
```

`answer` performs local inference using the existing configured endpoint. A returned assistant text with invalid JSON, answer structure, span selection, or citation capacity may receive one structural repair request; no third call is allowed. Transport failure, timeout, response overflow, cancellation, or tool-authority violations never authorize repair. The original rejected response is retained without quote normalization. Its optional question is controller input, limited to 2048 UTF-8 bytes; the default is the approved question. A different question reuses the same evidence without fetching. `replay` reads the saved answer and evidence without configuration, network access, or inference. It fails if either record is missing or altered. Both inspection and answer output identify the historical source version, retrieval time, and snapshot age. They do not establish current accuracy.

New answers use format3: the model returns each claim as exactly `{"text":"claim","spans":[1]}` with integer one-based source span IDs. The controller supplies the bound evidence ID and entire unchanged excerpt for each selected span, and derives displayed source URLs from the receipt. The saved/displayed canonical citation shape remains `{evidence_id, span, excerpt}`. The model never supplies quotations or URLs; there is no quote normalization or fallback to an older answer protocol. This proves citation provenance, **not logical support**: a human or independent semantic review must still check whether the cited text entails each claim. Unsupported questions should produce `insufficient_evidence` with no claims. Source text is untrusted data, including any apparent instructions embedded in it.

## Execution and storage bounds

Acquisition uses the already-installed pinned Python image with explicit `runc`, no image pull, a nonroot user, read-only root filesystem, dropped capabilities, 256 MiB memory, one CPU, 64 processes, and bounded temporary space. Only fixed helpers and approved inputs are mounted. The fetch executor has network access; extraction uses `--network none`. No project, credential, Docker socket, or GPU mounts are supplied.

The body limit is 2 MiB, framed metadata 8 KiB, extracted text 128 KiB, parser events 40,000 (extractor `document-text-v2`), nesting depth 64, and text spans 2,048. Exceeding a bound rejects the snapshot rather than truncating it. HTML script/style/template and other noncontent regions are discarded; assets and links are not loaded. UTF-8 HTML and plain text are supported.

Fetch work has a 15-second deadline and extraction 5 seconds. Each uses the existing guardian's bounded cleanup grace of at most 105 seconds (wait, forced cleanup, and pipe-reader joins). The acquisition publication fence includes both work deadlines and cleanup grace. Cancellation or owner loss triggers executor cleanup; incomplete records cannot be reused. Each answer call has a 120-second maximum child lifetime and at most 2,048 output tokens, medium reasoning, and 512 thinking tokens. The whole answer operation has a 260-second publication deadline, including both calls and process cleanup. Remaining time shortens a later call while reserving cleanup and publication time. Owner death kills the answer child; it cannot keep the store lease indefinitely. Cancellation refuses publication, including during repair or final staging checks.

New answers use format3 receipts: `receipt.json` is at most64KiB, with zero to two fixed `response-1.json` / `response-2.json` files, each at most64KiB. The receipt records the shared inference profile. Each attempt records its request hash, response hash/length when available, and structural validation result. A first-call transport failure has an attempt entry but no invented response file. The canonical answer is tied to the last validated response. The whole record is at most192KiB within the existing store budget. Oversized complete receipts fail closed; no claims or citations are silently dropped.

Normal terminal inference or validation failures save an immutable `answer_failure` diagnostic. The API raises `AnswerFailure` with an `identifier` attribute; the CLI returns1 and includes that identifier in its error. Use `documents inspect DIAGNOSTIC_SHA256` to inspect its attempt ledger. It cannot be replayed as a cited answer. A successful `insufficient_evidence` answer remains distinct and can be replayed normally. `inspect` exposes attempt metadata; fixed response files retain complete returned JSON for audit. Old format1 evidence/answers and format2 exact-quote success/failure ledgers remain readable with their original prompt, validation errors and request reconstruction; their bytes and identifiers are never rewritten. New calls have no user-facing protocol switch. Repair can alter claims, so review the whole final answer for support, omissions and unnecessary extras.

Format3 allows at most8 claims; each nonempty claim text must fit1024bytes as a canonical ASCII JSON string (including quotation marks and escapes). Each claim selects1–4 span IDs; at most16 occurrences are allowed across the answer. Duplicate references count each time. A selected whole span must fit2048encoded-string bytes and4096UTF-8 content bytes. All fields/counts/IDs/selected spans are checked before expanding citations. An insufficient-evidence reason must be nonempty and fit2048encoded-string bytes. The expanded answer is capped at48KiB, receipt metadata with only the answer removed at12KiB, and the final encoded receipt at64KiB. Metadata reserves both possible attempts and maximal bounded errors before inference; an oversized operator question/configuration fails explicitly without inventing a model response. Nothing is clipped or silently evicted.

All original spans remain in the evidence and request, including unselectable long spans. Selecting a long span is a structural capacity failure eligible for the same single repair. If *any* source span is too long for selection, an `insufficient_evidence` response is a capacity-unresolved failure, not accepted absence of support. A supported answer may still cite eligible spans. This conservative rule can reject a truly unsupported question because an unrelated long span exists; segmentation is deferred. Format3 inspection reconstructs its catalog/request and materialization from the fixed evidence and raw response, verifies the catalog/protocol binding, and compares the canonical answer. Literal references still require independent semantic review.

The private store is owned by the controller, mode 0700. Records have immutable-by-convention mode-0444 files, SHA256 identities, and verified byte hashes. This detects modification; it does not protect against an attacker who already controls the controller account. Publication waits for work cleanup and verifies the private staged record. It prepares display output, removes the staging marker, and syncs staging before one final atomic rename makes the record visible. No fallible filesystem work follows that commit. Existing valid snapshots survive a failed new publication. This is an atomic visibility guarantee; directory-rename persistence across sudden power loss is not certified.

The store refuses new evidence after 16 snapshots or when its 64 MiB budget cannot reserve 8 MiB staging headroom. It never silently evicts records. Interrupted staging or any nonzero executor outcome requires explicit recovery. The recovery marker is installed before launch and removed only after a successful executor result. Timeouts and cancellation can mask cleanup errors in the guardian status, so they conservatively keep the marker even when the container was removed:

```sh
python3 -m gflo documents --store .gflo/documents cleanup
```

Recovery removes only executors labeled for this store and unfinished staging/pending records; completed records remain. Preserve diagnostics before recovery when investigating failures. The complete research/search/browser qualification remains a later gate.
