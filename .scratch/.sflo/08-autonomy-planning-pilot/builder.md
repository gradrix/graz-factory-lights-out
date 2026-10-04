# Disposable planning harness handoff

Status: source frozen for independent controls and real Factory / prepared Docker synthetic-transport gate. No builder model, rig, serving, installation or maintained runtime changes.

## Boundary and behavior

Only `ops/planning_pilot_prototype.py` and `ops/test_planning_pilot_builder.py` are builder-owned, in worktree `gflo-planning-prototype`. The existing Factory, ModelWorker, Reviewer, environment resolver and guardian remain unchanged. The prototype subclasses/wraps only the necessary request, indexing, sandbox-attestation and supervision seams. Root owns cancellation driver and usage notes; independent QA/security own their tests and fixture corpus.

The four fixed serial arms share 48 charged completion attempts per arm across planner, plan review, workers, question assessment and code reviews. Debit persists before transport. Requests and bounded wire response bodies (including malformed/error bodies) remain outside worker mounts; missing usage is null. Over-cap bodies fail with explicit incomplete capture, never silently count as complete. One monotonic 1,800-second work deadline covers the arm subprocess; one 150-second cleanup deadline covers process-group shutdown, owned Docker removal/readback and fresh serving-idle probes. Deadline failures can advance only with positive cleanup/idle evidence; explicit cancellation stops the pilot. Existing output directories cannot resume/reset.

Decomposition has one proposal, one independent review, exactly two ordered scopes and fixed milestone/full checks. Both contexts retain every original requirement. Task1 acceptance is never increment acceptance. Full checks and an original-objective fresh review run identically after the final child of either method. After cleanup, parent rereads Factory acceptance and candidate identities before promotion.

The full task1 workspace is copied into a private clean Git checkpoint. Git control paths, links, special files/permission bits and oversized review inputs are refused before host Git. System/global Git config, templates, hooks and global attributes are disabled. Task2 pending workspace bytes/types/path set and executable bits must match before only recorded 0777 modes are restored; Git index/tree and base receipt are unchanged. Mode-map hash and before/after fingerprints are retained. Archive loss of empty directories or executable-bit changes fails explicitly rather than approximating the accepted checkpoint.

The existing guardian emits private creation inspection only after synchronous create succeeds. Each command additionally requires exact workspace-labelled container absence; missing creation or cleanup proof leaves a sticky fence and raises an unrecoverable controller error before another completion. This distinguishes ordinary failing application commands from ambiguous Docker create results. The executor guardian remains in its separate owner-EOF session when the controller group is terminated.

Serving probes are fresh bounded subprocesses, use the same expected private-config endpoint/model and compare exact allowlisted identity before/after GET. Raw slot list must have exactly one correctly typed id0/context98304/boolean-processing entry. Busy, unknown and malformed evidence cannot admit a new arm. A shared nonblocking lease serializes cooperating pilot/cancellation drivers; this is not a reservation against unrelated clients.

## Controlled evidence

`builder-controls.txt`: 10 passing controls cover exact mode restoration and original preservation, changed bytes/executable rejection, reserved Git paths, symlink/special-bit rejection, harmless inherited Git hook/filter/template isolation, malformed and HTTP-error raw bodies, overflow refusal, strict raw-slot types, normal-exit descendant termination and actual supervisor SIGTERM cancellation. No model or Docker calls in these controls.

Independent role/budget/plan/final-failure and security controls, plus synthetic prepared-environment integration, are separately owned and reported. Any gate defect will produce a new recorded source identity before inference.

## Limits and admission

No inference has run under this harness; no direct-versus-decomposed benefit is claimed. Actual GET readback and one controlled serving cancellation still belong to root admission. These two fresh cases cannot establish Stage5 qualification, a reliability rate or general integration safety. Complete transcript evidence is bounded to 4MiB per request / 1MiB per response; an oversize response preserves the bounded prefix and explicitly marks incompleteness. No semantic normalization, hidden plan rewrite, original-project merge or automatic parent resume is implemented.

## Necessary integration and publication repair

Independent QA exercised both decomposed cases on the actual approved rig environments using a synthetic completion transport: real Factory, offline Docker checks, prepared dependencies and checkpoint/mode restoration. Both passed (4.74s / 19.36s), with 13 synthetic charged requests each, final integrity true and executor absence confirmed. This validates wiring, not model behavior. The tested arm-work source was `162819c48a3449e00add6b7fb2232c11b6dff1a2c2188a5413fb8263ace135d9`, preserved at prototype commit `8d43977`.

Independent security then rejected that candidate for P08-PUBLISH: cancellation during final result preparation could leave a parent accepted result. Its red evidence remains `security-harness-publication-red.txt`. The successor changes only result publication: write/fsync the temporary record, check cancellation and shared work deadline immediately before atomic replace, rewrite as failed when success is refused. The exact published result feeds the aggregate. Successor harness hash: `b4e7beaab66c480f6e5f6a9a6daad6f57dbbdea6ce6b3ec4c88bafad599aafa9`. Builder10 controls still pass; independent final publication recheck is pending at this report update. No model exposure occurred during this repair.

## Final handoff

Successor mechanism preserved at prototype commit `d186b93`. Independent security18 controls PASS on exact successor bytes, including actual SIGTERM and deadline crossing during result temporary-file fsync, plus accepted control. Earlier failed candidate and red log remain preserved. Root reports fresh GET-only same-identity idle from the staged successor; builder made no serving or model calls. Final mechanism, test, fixture and controller-binding hashes are in `builder-candidate.json` (SHA256 `53f0d135065375a8c19db9dda67e6751d5840b4948f9a8a68344dabe905996bc`). Independent QA final report and actual cancellation / four-arm admission remain root-owned; no maintained source changes or qualification claim are implied.

## Combined test-isolation correction

The first combined run exposed test pollution: the imported QA arm_work control retained sanitized Git environment variables, defeating a later security positive control. QA/security changed only their test isolation. The final combined52 controls PASS in5.789s (`combined-controls-recheck.txt`; exact copy `combined-controls-final.txt`). No mechanism change or unrelated rerun occurred. Synthetic/model qualification limits above remain unchanged.

Original manifest retained as `builder-candidate-before-test-isolation.json`, SHA256 `53f0d135065375a8c19db9dda67e6751d5840b4948f9a8a68344dabe905996bc`. Refreshed `builder-candidate.json` SHA256 `8ca88802c147f89e2c1528fba5280b161d159aeb71eb86c0c658c7875393e186` binds the two corrected test files; harness remains `b4e7beaab66c480f6e5f6a9a6daad6f57dbbdea6ce6b3ec4c88bafad599aafa9`. The mechanism commit remains d186b93; root owns the subsequent evidence/test commit.
