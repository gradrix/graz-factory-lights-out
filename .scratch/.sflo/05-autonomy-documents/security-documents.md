# Independent security assessment: document evidence candidate

2026-10-02. Skill: security-check. Candidate manifest: [original candidate manifest](security-documents/original-candidate.json), SHA-256 **`fba3e2f5fe14c640818808b32242c617b7a2ed78c3b2fbb332e7080764b6f336`**, baseline `410a46277af9beb0643af7bee1544380f5f687fb`, nine changed files; subsequently preserved as Git commit `dc60ee3`. [Frozen contract](contract.md); [boundary proposal](../../autonomy/document-evidence-boundary.md).

## Outcome

**REPAIR REQUIRED: two actionable lifecycle/publication findings.** Controlled local reproductions show (1) a failed acquisition can leave a newly resolvable receipt after final-sync plus retirement failure, and (2) some cleanup failures do not block new work pending recovery. Prior valid evidence remains intact in the publication probes. These results prevent a passing security verdict for this candidate despite passing input/authority controls and separate functional QA.

## Coverage and method

I inspected all new security-sensitive source, the CLI/worker changes, and maintained document test source. The nine candidate hashes match before and after my assessment ([before](security-documents/hashes-before.json), [after](security-documents/hashes-after.json)). Tests load a private frozen copy in ignored `.gflo/security-documents/fba3e2f5/`; maintained product/test files were not edited.

My measurements use fixed local data, injected executor results, actual disposable Python children, and temporary private stores. No real Docker operation, network request, model call, GPU work or shared-service mutation was performed by this reviewer. [Functional QA](qa-documents.md) independently supplies real approved-source acquisition, offline extraction/container facts, live fetch-owner SIGKILL and extraction cancellation. I read that report; its measurements are not my own rerun evidence. The builder/rig model semantic gate is separate.

### D1 — Failed publication can leave a reusable new ID

**Medium severity; high confidence, reproduced.** Affects `gflo/documents.py:303` `_publish` sequence: after private verification/cancellation fencing it removes `pending`, then calls `sync_directory(destination)`. If that sync fails, the exception handler attempts to rename the destination back to private staging. If that retirement rename also fails, the ID remains published without `pending`; `resolve()` accepts it even though acquisition raised.

[Probe](security-documents/probe.py), [results](security-documents/results.json), case `final-sync-and-retirement-failure`: two controlled filesystem errors produce an exception and exactly one new resolvable ID. The original receipt and every original published file hash remain unchanged. Conforming control publishes successfully; isolated final-sync failure retires correctly and leaves no new ID. This is an ordinary combined I/O-failure path, not an attack requiring a privileged concurrent writer.

Impact: the failed attempt can later be used as completed evidence, violating the receipt's publication/cleanup contract. Same `_publish` seam also handles answer receipts. Smallest repair direction: keep non-reusability through every fallible precommit operation; make final eligibility removal the actual commit without subsequent fallible operation that can turn success into failure, or durably fence uncertain publication before exposing it. Preserve prior good. Also review the caller's postcommit `stage.exists()` checks against this invariant; the reproduced defect above is the sync/retirement path.

### D2 — Cleanup failures can lose the recovery requirement

**Medium severity; high confidence in controller composition, reproduced with controlled executor outcomes.** Affects `gflo/documents.py:228`: `_execute` creates `.cleanup-required` only for `RuntimeError` or primary exit code 125.

Two real guardian interfaces can communicate cleanup uncertainty differently:

- Docker cleanup subprocesses can raise `subprocess.TimeoutExpired` (or an OS exception), which is not `RuntimeError`.
- `guard.run` overwrites the primary result with 124/130 for timeout/cancellation, even when the guardian returned cleanup-failure 125; the cleanup diagnostic remains in output.

[Probe/results](security-documents/results.json) cases `cleanup-timeout-exception`, `cleanup-failure-masked-by-timeout`, and `cleanup-failure-masked-by-cancel` feed those controlled outcomes into actual acquisition. Each acquisition fails but creates no recovery marker; a subsequent valid acquisition publishes without calling explicit cleanup. The exit-125 control correctly writes the marker and refuses retry. These are synthetic interface failures, not an induced Docker daemon outage or an observed surviving real container in this assessment.

Impact: an uncertain owned executor can coexist with later work, defeating the promised recovery/admission boundary and potentially accumulating resource use through retries. Smallest repair direction: carry cleanup success/failure separately from the primary operation outcome, or conservatively require explicit recovery for uncertain executor failures. Do not classify cleanup solely from the primary exit code or parse human log strings as the long-term protocol. Retest failure + blocked retry + successful explicit recovery, retaining prior records.

## Assessed controls

[Independent coverage probe](security-documents/coverage.py) and [results](security-documents/coverage-results.json) retain the following passing checks:

| Boundary | What the evidence establishes |
| --- | --- |
| Approval/authority | Nine malformed or disallowed URL forms reject. Controller approval supplies exact URL; the model never chooses or changes it. Approved hosts are intentionally not the package registry allowlist. Package mandatory digests/allowlist remain unchanged. |
| DNS/TLS | Seven nonpublic/mixed/empty IPv4 answer sets reject before connection. A valid public control resolves. Injected certificate failure verifies numeric connection address, original hostname passed to TLS and socket closure; no endpoint contacted. Reused `fetch.Connection` uses a validating default TLS context, explicit sockets and no proxy/redirect machinery. |
| Framing/retention | Exact 2 MiB and limit-minus-one controls qualify; added/truncated bytes reject. Frame URL/status/length/address disagreement, expected-hash mismatch, duplicate JSON fields, nonfinite JSON and header limit violations reject. Fourteen retention/encoding/attachment/cookie variants reject. Source requires Content-Length and EOF, so a peer retaining an open connection can consume its deadline but cannot qualify incomplete evidence. |
| Offline untrusted text | Nine excluded HTML regions are omitted; visible hostile instructions remain text. Depth/event/block/byte/UTF-8/NUL controls reject. Source uses an offline fixed parser and does not execute assets/scripts. Actual extraction/container boundary checks belong to functional QA. |
| Immutable evidence | Eight content/mode/link/extra/pending tamper variants reject. Cancellation becoming true after root sync, before commit, leaves only prior good. No untrusted host writer is assumed; store root/modes and exclusive/read leases enforce the intended local owner boundary. |
| Tool-free answer and citations | Request contains neither tools nor functions and uses a fresh two-message context with frozen evidence ID/spans. Invalid ID/span/quote/model-supplied citation URL reject. Tool/function output rejects before publication; output has no execution dispatch. Saved display URL comes from approval. Exact excerpt membership proves provenance only; a supported-looking false claim with a genuine quote still needs semantic QA. |
| Answer process lifetime | Positive child, response-size failure, client exception and cancellation pass. Actual owner SIGKILL makes the controlled answer child disappear and releases its inherited lease. The fork-to-parent-death race has an explicit parent PID check. No model server was invoked. |
| Credentials/devices/resources | Personally inspected fixed executor arguments: pinned Python image, no pulls, runc, caller nonroot UID/GID, read-only root/binds, dropped ALL capabilities, no-new-privileges, 256 MiB memory/swap, 1 CPU, 64 PIDs, bounded shm/tmpfs, bridge for fetch and none for extraction. Only approved/helper/body files are mounted. No project/home/credential/socket/device mount is supplied. Actual inspected facts are separate QA evidence; source requests alone are not measured enforcement. |

The local answer child is trusted controller code using the existing loopback-only client; it can read the explicitly configured inference key on the host. That key is not mounted in fetch/extraction or included in the answer receipt's endpoint/model-only config. Untrusted source text has no tool/capability route. The small worker change bounds response bytes when requested and retains its prior default behavior for unrelated calls.

## Inference boundaries and remaining qualification

The output limit, local-only endpoint validation and child lifetime are assessed without inference. This does not establish that the actual model will answer correctly, resist every persuasive instruction semantically, or choose insufficient evidence appropriately. Citation checks enforce source membership, not entailment. Saved replay checks immutable evidence and does not create a client or refetch; new answer attempts remain separate inference operations.

Real remote DNS/TLS/registry outages, hostile public sites, kernel/container escapes, power-loss durability, and malicious privileged host writers are outside these controlled checks. Independent functional QA supplies the authorized live documentation path and real container lifecycle. The unmodified 120-second deadline terminated a sleeping fake client after **120.005 seconds** with a work-deadline error ([measurement](security-documents/deadline-result.json)). This is actual local child supervision, not a model-server timeout measurement.

Repair and refreeze before acceptance; independently renew the affected publication/cleanup controls and source hashes. No full Stage 4 research/browser acceptance follows from this first slice.

## Reproduction

The retained scripts reconstruct original `dc60ee3` from Git into the ignored private directory and verify the candidate manifest/source hashes. They require Linux/Python with fork and local Git history. No network or Docker is used; only test-owned processes are signalled. The fault probe intentionally asserts that the original defects remain reproducible.

```sh
python3 .scratch/.sflo/05-autonomy-documents/security-documents/probe.py
python3 .scratch/.sflo/05-autonomy-documents/security-documents/coverage.py
python3 .scratch/.sflo/05-autonomy-documents/security-documents/coverage.py --deadline
```

The last command takes approximately 120 seconds. Existing original results are retained evidence; save copies before rerunning if preserving their exact temporary IDs is required.
