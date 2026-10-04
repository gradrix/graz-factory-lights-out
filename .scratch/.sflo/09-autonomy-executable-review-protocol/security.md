# Executable-review protocol successor: independent security assessment

## Outcome and binding

**PASS for the frozen source and local controlled security scope.** No unresolved material security finding remains. The separately required actual synthetic phase-wiring gate and once-only trial admission remain coordinator responsibilities; this report is not an inference authorization or a model-quality verdict.

- Contract SHA256: `f4381c22e730f53bd5bab1af93e4794aa4c83fe0ce31c2a1a2767fc9a51a076f`.
- Driver: `ops/executable_review_prototype.py`, SHA256 `c69e90f8359603b9bf6636fa02a6b0887a4ba2af38f9f481243f9c8e831530a8` in `/home/gradrix/repos/gflo-review-protocol-prototype`.
- Independent controls: `ops/test_executable_review_security.py`, SHA256 `8f9fbd7ec791bf9f08a8cf929a88fe5b1f4b060b40b08787006791af47c4b612`.
- [Final binding](security/final-binding.json) records identical before/after hashes for the driver, own tests and all 32 reused source/assets. [Forty-one controls](security/final-controls.txt) passed in 0.875 seconds.

Reproduction: `python3 .scratch/.sflo/09-autonomy-executable-review-protocol/security/verify.py /home/gradrix/repos/gflo-review-protocol-prototype` from the main checkout. This runs only fake-transport/guardian and local file/signal controls, without Docker/model/service operations.

## Finding closed before exposure

**P09P-LENGTH-ENVELOPE — closed on the assessed driver.** Draft SHA `bcde9f5482b12120d5788ef5a17d861ffff503a355377598b8289ece709aed02` checked collection type after the length-recovery branch. A `length` response whose `tool_calls` was an object, including an explicit unknown function name, could consume recovery and issue another request. This violated the specified terminal treatment of malformed authority. It did not execute a command or replenish the total budget.

The independent [red control](security/length-envelope-red.txt) reached a second transport, exhausting the deliberately one-response fake sequence instead of raising the required authority error. The repaired driver validates the call collection before recovery. A supplied follow-up response cannot cause a second request; recovery remains unused and no command executes. [Focused green](security/length-envelope-green.txt) and the final 41-control run close the finding. Earlier `first-controls.txt` observed an incomplete ledger/loop implementation during construction; those are not frozen-candidate defects.

## Personally executed controls

| Boundary | Direct evidence |
|---|---|
| Shared request accounting | Seven exploratory attempts reserve the eighth for one final call. Failed transports retain charges. Reconstruction cannot repeat finalization or recovery. A ninth request never reaches transport. |
| Recovery eligibility | A truncated batch containing a valid run and incomplete run arguments executes zero commands. One recovery is allowed; a second truncation is terminal, including at the seventh credit. Explicit unknown tools remain terminal even with `length`. Nontruncated malformed/unknown batches execute no valid prefix. |
| Phase authority | Exploratory prose triggers a separate final request and is never accepted as the verdict. Final request has `response_format=json_object` and no tools/tool choice. Command reservation after transition is forbidden. No attestation prevents final transport. |
| Time reservation | Exploration request and command timeouts shorten to remaining phase time; final timeout is at most 120 seconds within the overall deadline. A late exploratory response starts no command. A mid-batch boundary retains only executed calls and matching tool replies, preserving the full original response and explicit skipped-call evidence. |
| Terminal errors | Transport timeout and uncertain executor creation/cleanup are terminal, not recovery or scheduling transitions. Final tool calls, wrong-type falsey call collections, length truncation and fenced JSON are rejected without salvage or retry. Overall expiry during final response prevents a verdict artifact. |
| Publication | Actual local SIGTERM and controlled deadline crossing at final pending-file fsync prevent accepted publication. Paired conforming control succeeds. Unknown pre/post serving idle or cleanup state stops later cases. |
| Executor seam | Positive started exit-1 command remains failed-check evidence. Missing nonce/creation, writable mount readback, missing memory limit and uncertain cleanup fail closed. Root UID is refused; links/hardlinks/FIFOs are rejected. |

The successor does not treat a command's nonzero exit as uncertain lifetime when positive start, creation and confirmed absence are available. The unchanged executor can similarly retain an attested timeout/output-limited result as a failed or partial check; it does not thereby establish successful tests. Missing or uncertain lifecycle proof raises a terminal error. Independent semantic scoring must check any claim of passing tests against the actual output.

## Explicit carry-forward and scope limits

[Carry readback](security/carry-readback.json) independently verifies all 32 reused whole files and exact source spans of nine unchanged definitions: `CommandExecutor`, tool/schema helpers, source/manifest validation, exact-owned removal, case setup, cleanup and CLI. New wiring is tested directly; the full driver is not called unchanged. The unchanged executor receives a different phase-aware ledger deadline, which has its own timeout-clamp control. The batch changes only experiment metadata; its previously qualified supervisor, shared lease, final publication and idle/cleanup flow remain intact.

Prior unit09 actual read-only Docker and synthetic rig evidence and unit08 helper cancellation evidence are carried only through those verified identities. This review performed no new actual Docker timeout/output/owner-death test. The successor's three-response synthetic phase driver is a separate required gate; no real-model repair claim follows from controlled responses. The combined local suite reports 62 collected, 61 passed and one unchanged actual-Docker control skipped; it is not represented as 62 newly executed passes.

The controller, local evidence ownership and Docker daemon remain trusted. No hostile host writer, shared-daemon outage or supervisor SIGKILL qualification is claimed. Source/tool output stays untrusted data. Raw response and request caps remain 1 MiB/4 MiB. Retained output is bounded before replacement decoding; the predecessor report's distinction between raw bytes and decoded representation still applies. The initial failed trial and its three incomplete results remain immutable; this successor requires its own frozen admission and results.
