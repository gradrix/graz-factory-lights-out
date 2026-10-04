# Planning pilot serving lifecycle route

2026-10-04. Read-only assessment against accepted runtime `92deaab`, published `c81429b`, and [unit08 contract](contract.md) SHA256 `d52ae8c2f322f417fed6c8cf6ace5343720cc40f86f0d0aeb6b9294e2fc33bea`. Applies the security-check skill. No maintained source edits, inference requests, restarts, serving changes or other application operations.

## Outcome and coverage

**A positive serving-idle observation route is available on the current owned server.** Fresh authenticated GET `/slots`, combined with exact serving identity and strict parsing, can support admission and cleanup checks without changing the service. This is a discovery result, not permission to start the four arms or proof that client cancellation stops generation. Frozen harness review and controlled cancellation/deadline evidence remain required.

Measured here: safe Docker readback before/after; six bounded authenticated GETs at the idle endpoint; current ModelWorker, reviewer, Sandbox and guardian source inspection. Not measured: busy endpoint behavior, request cancellation, server queue drain, outer-supervisor implementation, daemon outage or abrupt controller cleanup. The proposal below must be implemented only in the disposable prototype and verified before inference.

## Actual idle facts

[Sanitized observations](serving-lifecycle/actual-idle.json), collected `2026-10-04T16:37:49Z`, are reproducible with the [GET-only script](serving-lifecycle/read-only.py) through `ssh -o BatchMode=yes -o ConnectTimeout=10 monster-gaming-pc.lan python3 - < SCRIPT`. The script reads the private key in memory, disables proxies/redirects, caps each response at64KiB and uses five-second socket timeouts. Its saved output contains selected public identity/state fields only. It is a discovery script, **not an admission executable**; the supervisor must separately enforce an absolute invocation deadline.

| Fact | Observation |
|---|---|
| Owned container | `gflo-model`, label `gflo.owner=model-service`, running |
| Container ID | `2cac4229053dac00fdbcadb1952db80f0a9da3fd07b8f40bce1ba8cd3114f6e0` |
| Image | `sha256:249ed60fdd67b96db472e16f945af5aaba565b20159d192ba378035b6d136a1c` |
| StartedAt | `2026-10-04T14:20:09.194925789Z`, unchanged before/after |
| Profile flags | alias `flash-next-coder`, context98304, parallel1, K/V `q4_0`, offline |
| Binding | host `127.0.0.1:18000` → container8000 |
| Runtime path | `/model/runtime/llama-b11284/llama-server` |
| Key mode |0600; contents never output |
| `/health` |200, `status:"ok"`; idle/processing counters absent |
| `/slots` |200; exactly one slot, integer `id:0`, integer `n_ctx:98304`, boolean `is_processing:false` |
| `/slots?fail_on_no_slot=1` | Same200 and idle slot |

The three GETs were repeated one second apart with the same results. The path identifies the intended runtime release; no new binary-hash attestation was performed. Raw slot settings/prompts/cache fields were discarded rather than copied into evidence.

The official pinned-release documentation describes `/slots` as current processing-state monitoring, enabled by default, and documents503 for `fail_on_no_slot=1` when no slot is available. This agrees with observed availability despite no explicit `--slots` flag. It does not establish cancellation semantics. [llama.cpp b11284 server documentation](https://github.com/ggml-org/llama.cpp/blob/b11284/tools/server/README.md#get-slots-returns-the-current-slots-processing-state).

## Small fixed probe interface

Builder owns the frozen controller-side executable. Invoke it freshly before and after each arm, outside worker mounts, with no model-selected command/path/URL. Return bounded JSON such as:

```json
{"version":1,"idle":true,"server_identity":{"container_id":"...","image":"...","started_at":"..."},"health_status":"ok","slots":[{"id":0,"is_processing":false,"n_ctx":98304}],"observed_utc":"...","reason":"observed_idle"}
```

Require exact booleans and integers, not truthiness (`false` is not equivalent to missing/null/0/string). Require exactly one dictionary slot, id0, context98304, `is_processing is False`, health200/statusok, expected running container/owner/image/start/profile and loopback binding unchanged before/after the GETs. Unknown structure, absent fields, auth failures, redirects, oversized/malformed JSON, unexpected statuses, identity changes and probe timeout cannot return idle. A valid busy slot is `idle:false`; unknown must carry a distinct reason and also refuse admission. Validate raw list membership before selecting safe fields; never drop malformed entries then classify the shortened list idle.

Keep authentication entirely inside the trusted probe. Do not retain HTTP error bodies, key/config dumps, complete Docker commands/environment or slot parameters. Bound stdout/stderr and the entire subprocess duration (e.g.15seconds, shortened to remaining cleanup time), independently of HTTP socket timeout. Return only selected safe fields. A saved idle file is historical evidence and never clearance; controller accepts only its own just-completed invocation. Two separated fresh idle samples provide a useful settled-state check but are not a reservation or a proof against an unrelated client racing afterward.

This route assumes exclusive experiment ownership of the serving endpoint and serial completion dispatch. Hold a controller lease across all pilot arms; prevent overlapping local pilot processes. Do not claim that this lease controls arbitrary external clients or that `/slots` exposes a complete request queue. If concurrent use is known or suspected, refuse the next arm. No slot erase, unload, restart or other POST is part of cleanup.

## Reuse and missing lifecycle guarantees

- `gflo/worker.py:ModelWorker.request` is the correct shared completion seam: loopback HTTP only, proxy disabled, redirects refused, private key loaded only for transport. It supports a response byte cap, but ordinary worker requests currently omit that cap. The prototype must provide a fixed response cap sufficient for its raw evidence and refuse overflow. Its timeout is a socket operation timeout, not an absolute1800second supervisor.
- Worker attempts currently get separate1800second timers. Reviewer/question assessment also call the client, including120second review calls. A single wrapper must reserve and durably record each of48completion requests **before transport**, cap timeout to shared remaining time, enforce profile limits and prevent child/planner/reviewer bypass. Failed transport and interrupted calls remain charged. Child creation cannot reset the pool. GET observations are not completion requests.
- `gflo/guard.py` uses an independent session and owner pipe EOF to remove its owned executor. It does not supervise the model service. Killing the client/controller cannot be relabeled as positive serving-idle evidence.
- `Sandbox.cleanup` queries exact workspace labels then removes found IDs. Return success alone does not provide a final absence readback or resolve a potentially in-flight Docker create. Parent cleanup needs exact-owned scope, final readback and conservative unresolved status on creation/transport/daemon uncertainty; do not touch shared serving or unrelated jobs.

## Absolute work and cleanup boundaries

1. Freeze baseline, probe, harness, fixture/environment identities, request caps and serving identity before arms. Fresh idle observation is required before dispatch; baseline evidence is not reusable clearance.
2. Supervisor lives outside the arm's process group and starts a monotonic1800second work deadline before any arm planning/review/checkpoint work. Worker, planner, reviewer, assessment, tooling and handoff share it. Only the supervisor may publish a parent outcome; gate success again against cancellation, deadline and candidate identities after child completion. A child finishing at or beyond the deadline never creates parent success.
3. On cancellation/deadline, permanently close dispatch and mark interrupted/failed. Terminate owned controller/client descendants (bounded TERM then KILL as needed). Preserve guardian owner-EOF behavior and wait for its owned cleanup; avoid a surviving descendant holding the owner pipe open. The separately frozen test must exercise this, not infer it from a Python exception.
4. Start one150second cleanup deadline at the work-stop transition. All waits, owned-executor removal/readback and fresh idle polling consume this same allowance; do not grant150seconds per operation. Use remaining time for every subprocess/socket bound. Poll positive slot-idle evidence only after request-producing clients are dead. A bounded fresh probe must fit within the remaining allowance.
5. By expiry, either record confirmed owned cleanup plus fresh same-identity idle observations, or record unresolved cleanup/serving state and stop the pilot. Never start another arm after uncertainty. Even successful cleanup cannot convert an interrupted arm into success. A retry requires a newly labeled experiment.

## Frozen checks required next

Use controlled clients and disposable repositories to cover busy, missing, malformed, oversized, wrong-type and stale-idle responses; changed serving identity; probe timeout; all roles charged; extra-request denied before transport; no budget reset; deadline during model wait/tool/checkpoint; cancellation before final publication; child death with a guardian; cleanup uncertainty; and task1 acceptance followed by task2/full-check failure. Verify original/prior-good hashes and bounded evidence retention. Existing trajectory truncation means it is not sufficient as the only record where the pilot requires full raw requests/responses; enforce an explicit size/refusal policy in the outer capture.

After that candidate is frozen and independently reviewed, a **separately authorized** bounded real request interruption can measure whether killing its client actually transitions the pinned service from busy to idle within the common allowance. Until then cancellation behavior remains unverified. If this probe cannot establish idle, preserve failure and stop without service changes.

## Prototype boundary review

The current [route](../../autonomy/planning-prototype-route.md) and contract correctly restrict model output to two ordered assignments and preserve fixed external acceptance. The serving additions above are necessary concrete mechanisms, not a new maintained framework. Remaining implementation review must establish that: plan text cannot change tools/checks/environment/permissions; full raw evidence and journal are outside worker mounts; handoff is a verified fresh snapshot with original accepted requirements; the same frozen full acceptance decides both arms; outer outcome cannot inherit child success after expiry; and ambiguous cleanup never unlocks another arm. No defect is asserted in an unfrozen harness; these are acceptance obligations communicated to the builder.
