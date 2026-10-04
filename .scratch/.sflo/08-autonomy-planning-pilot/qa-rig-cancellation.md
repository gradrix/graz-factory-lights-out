# Independent readback: one real serving cancellation probe

2026-10-04. **PASS against the narrow cancellation contract.** The persisted sequence supports deliberate termination of the owned request client followed by confirmed process-group absence and settled idle on the unchanged server within the allowance. This is independent review of coordinator-run measurements, not a second live execution. No endpoint, model, Docker or service operation was performed during this review.

## Binding and admission

- Frozen prototype commit `d186b9330b7b9916e06b3807f1ea03adc02943e8`.
- Driver SHA256 `eef6fba8f02498c2c247f2d264a1dca5bbf2bb5caec5521db97f63a29b443128`; harness SHA256 `b4e7beaab66c480f6e5f6a9a6daad6f57dbbdea6ce6b3ec4c88bafad599aafa9`.
- [Admission](cancellation-admission.json) SHA256 `69d38f8aa5bd597fbefd239707fdbe3a49ccee01097134127aa5daf33ce7c689`. Its32code hashes match exact local commit contents; contract, combined52controls, coordinator decision and expected-identity hashes match their saved bindings.
- Cancellation contract SHA256 `992ed9637b164e68cf3093cca817938ccd7ec31593813b789e69927964c8d7c9`. Admission binds the fixed loopback public profile and shared lease. The driver copy of admission is identical JSON; its serializer omits the original trailing newline, so the copy has a distinct recorded byte hash. This is expected serialization, not changed admission content.
- The saved benign counting request matches admission request hash `2955876916f93a2d1fdccd0f024e5598d9736f040b5604f0821a84bfa8b44a7f`: medium reasoning,4096output/1024thinking, temperature0, no tools or project/private data. Debit count/limit are both1 and its monotonic time precedes the matching client's start record. The reviewed driver has a single ModelWorker request invocation and no retry path; this review does not add packet-capture proof.

[Readback checks and hashes](qa-rig-cancellation-readback.json), [reproduction script](qa-rig-cancellation-readback.py), [raw events](rig-cancellation-1/events.json), [result](rig-cancellation-1/result.json).

## Observed chronology

| Elapsed seconds | Persisted observation |
|---:|---|
|0.1140|Fresh healthy same-identity idle slot|
|1.2316|Second idle observation;1.1175seconds after first|
|2.2472|Owned client PID19741 launched|
|2.6147|Strict positive busy slot (`is_processing:true`)|
|2.6180|Stop transition: client alive, no completed response, busy observed|
|2.6720|SIGTERM, return code−15, owned process group absent|
|2.7890|Server still busy after client-group removal|
|3.9068|First idle observation after stop|
|5.0253|Second idle observation;1.1185seconds after first|

Final recorded elapsed time is **5.0288seconds**, cleanup **2.4109seconds**, both within60second work/150second cleanup limits. No response or client-complete record exists. This supports interruption before normal client completion rather than an inconclusive completed-response race. Result `cancelled:false` refers to no external cancellation of the probe supervisor; deliberate SIGTERM of its child is separately recorded.

All six serving observations carry identical expected container/image/start/profile identities: container `2cac4229053dac00fdbcadb1952db80f0a9da3fd07b8f40bce1ba8cd3114f6e0`, image `sha256:249ed60fdd67b96db472e16f945af5aaba565b20159d192ba378035b6d136a1c`, start `2026-10-04T14:20:09.194925789Z`, one98304context Q4/Q4 slot, owned model-service, offline serving and loopback host binding. No restart or profile transition appears in the sequence.

## Interpretation and limits

The lifecycle prerequisite passes for this one bounded request on this pinned service. The busy observation after client removal directly confirms why client death alone cannot establish serving idle; the later two fresh observations provide the required positive evidence. They show a bounded transition following disconnection, not the server's internal cancellation reason or universal cancellation reliability.

The shared lease and consumed-admission behavior are supported by the reviewed frozen driver and controlled tests; this readback did not inspect the live rig lease/marker again. No actual daemon outage, server SIGKILL, supervisor SIGKILL, arbitrary concurrent client, repeated cancellation, long-running project arm or general reliability claim follows. Historical idle evidence cannot clear a future arm: each arm must obtain its own fresh strict preflight and cleanup observations. The four-arm frozen admission and independent full-result review remain separate controller gates.
