# Incremental autonomy qualification

## Visibility and controlled operation — accepted

Candidate `18a274f`; independent review and real RTX 5090 trials, 2026-10-02.

| Actual local-model task | Interruption | Accepted attempt | Elapsed |
| --- | --- | ---: | ---: |
| Invoice decimal CLI | Targeted cancellation, then resume | 2 | 136.4 s |
| Inventory utility | Controller SIGKILL, then resume | 2 | 165.5 s |
| Log summary CLI | None | 1 | 74.2 s |

Every run had exactly one durable acceptance event. A second HTTP client observed execution. Independent real-Docker probes checked killed/cancelled writers, recovery, event replay, evidence integrity, read-only HTTP boundaries, redaction/truncation and startup cancellation. Chromium checked desktop light/mobile dark, artifact navigation, disconnect/reconnect and empty-state behavior.

Three QA findings were repaired: fresh-state API failure, false pending state after startup cancellation, and lost `--rm` command arguments in the guardian. Container creation is completed before starting any writer. Final guardian tests also passed on the rig. Source used by the initial model trials was `3c3a834`; subsequent repairs were rechecked within their affected scopes through the accepted candidate.

[Independent acceptance](../../.scratch/.sflo/02-autonomy-visibility/qa-accepted.md), [rig receipt](../../.scratch/.sflo/02-autonomy-visibility/rig-trials.json), [final rig guardian checks](../../.scratch/.sflo/02-autonomy-visibility/rig-guardian-final.txt), [coverage](../../.scratch/.sflo/02-autonomy-visibility/coverage-final.txt).

## Independent local review — accepted

Accepted candidate **3bd8ae2**, 2026-10-02. Actual local-model cohort D ran on **4346ba5**; later changes repair display/trace redaction and promote the already-tested default profile. Model prompts, reviewer and controller acceptance logic did not change after that cohort.

| Gate | Observed result |
| --- | --- |
| Frozen reviewer defect/control set | Flash caught10/10 seeded defects, all critical, with2 false blocks and0 format failures; supplemental known defect caught. |
| Equal-budget dense reviewer comparison |7/10, critical miss,4 invalid assessments; Flash retained. |
| Fresh coding cohort D | **12/12 accepted**, all repeated executable checks and independent semantic checks passed. |
| Separate product ambiguity | Correct `needs_input`; no invented allocation implemented. Question wording still included unnecessary policy detail. |
| Real repair | D09 repaired a failing generated CLI test on attempt2. Earlier B11 demonstrated genuine reviewer findings and repair; unchanged-component continuity was independently checked. |
| Lifecycle/privacy regressions |59-test whole suite,88%coverage at89d66ea; subsequent parity repair passed21 affected tests and independent HTTP/worker probes. Promoted image passed8 sandbox/qualification tests. |

Qualified serving is the installed Flash-Next Coder export, one serialized local request, **131072 context**. Coding requests use medium reasoning with a requested1024-token thinking budget inside4096 total output tokens. Sandbox runtime is independently measured **Python3.12.13**, imagefb1118f… . The server does not separately report actual reasoning-token consumption.

D used182 coder calls, a maximum27628 prompt tokens (median8632), median65.8 generation tokens/s, and2910.67seconds total task wall time (about49minutes). All565 trajectory lines parse as JSON. These measurements exclude reviewer/question-assessment calls from token statistics and do not qualify128K problem solving.

**Remaining quality limitations:** D06 review wrongly rejected a correct tie-break and caused unnecessary repair. D09 retains a minor README escaping error. D05 tests assume `/workspace`; several outputs contain unnecessary validation or test-quality residue. Ambiguity wording suggests an unstated partial-payment rule even though it correctly stops. No accepted critical or substantive functional miss was found, but twelve bounded tasks are a qualification floor, not proof of reliable large-project autonomy.

[Full independent D evaluation](../../.scratch/.sflo/03-autonomy-review/qa-coding-d.md), [raw result](../../.scratch/.sflo/03-autonomy-review/coding-d.json), [runtime identity](../../.scratch/.sflo/03-autonomy-review/coding-d-runtime.json), [metrics](../../.scratch/.sflo/03-autonomy-review/coding-d-model-metrics.json), [review-loop continuity](../../.scratch/.sflo/03-autonomy-review/qa-review-loop-continuity.md), [final privacy recheck](../../.scratch/.sflo/03-autonomy-review/qa-nested-verdict-parity-recheck.md).

### Preserved failed trials

A finished7/12; B had11 raw acceptances but only9 deliveries without identified requirement gaps; C finished9/12 and failed its gate. Their scores were not rewritten. Earlier trials used Python3.11.15 despite later objectives targeting3.12; separate3.12 checks do not retroactively correct execution. A paired repeated-case probe then repaired2/2 known failures with bounded medium reasoning versus0/2 without reasoning. That small experiment motivated fresh D; it is not an unseen success rate.

[Execution history and repairs](../../.scratch/.sflo/03-autonomy-review/run.md), [C semantic evaluation](../../.scratch/.sflo/03-autonomy-review/qa-coding-c.md), [runtime provenance correction](../../.scratch/.sflo/03-autonomy-review/qa-runtime-provenance-addendum.md), [paired repair evidence](../../.scratch/.sflo/03-autonomy-review/qa-repair-reasoning-results.md). Earlier independent Docker checks that used the local default runtime establish functionality, not GPU isolation; later receipts explicitly select runc.

### Reproduce D as a repeated trial

```sh
python3 ops/prepare_qualification.py .gflo/repeated-d --source evaluations/coding-d
PYTHONPATH=. python3 ops/qualify_coding.py .gflo/repeated-d .gflo/repeated-d-results
```

Use the qualified configuration and installed pinned image. Existing destinations are refused. Published hashes identify the original model-visible inputs; new Git commit metadata can differ. Acceptance checks remain outside the writable worker mount. These now-known cases cannot be labeled unseen in a rerun.

## Supported environments — accepted

Runtime **25f75c3**, serving manager **8fdde15**, 2026-10-02. Three profiles passed cold package-cache preparation and two fresh offline smoke checks each on the rig; pinned base images were already installed. Independent input, artifact, lifecycle and publication checks passed. The complete runtime gate passed88 tests at85% branch-aware coverage.

The original128K/Q4 coding cohort remains **1/3 accepted**: stdlib passed; API and Node exceeded their frozen budgets. Independent review found genuine documentation omissions and two oracle defects. Those outcomes were preserved. Distinct API and TypeScript follow-ups used corrected, independently checked oracles and96K/Q4:

| Task | Accepted attempt | Elapsed | Independent semantic result |
| --- | ---: | ---: | --- |
| Original stdlib |1|482.71s|Passed |
| Fresh telemetry API |1|285.71s|100 domain cases,15 HTTP cases and README commands passed |
| Fresh availability TypeScript CLI |2|178.41s|150 interval cases,10 CLI cases and relocated README commands passed |

The Node follow-up automatically repaired an empty first attempt. These qualify three profile paths, not a3/3 original cohort or general project autonomy. The accepted runtime was installed at `MONSTER-GAMING-PC:~/gflo-runtime`, preserving state/config.

A fixed16947-token input measured roughly74 generation tokens/s at96K/Q4 versus16.5 at128K/Q4. An81441-input-token retrieval check passed three exact lookups; this does not establish full-window coding quality. The default is96K/Q4;128K remains an explicit option.

[Acceptance](../../.scratch/.sflo/04-autonomy-environments/acceptance.md), [original cohort](../../.scratch/.sflo/04-autonomy-environments/rig-model-25f75c3.json), [API semantic QA](../../.scratch/.sflo/04-autonomy-environments/qa-model-api-followup.md), [Node semantic QA](../../.scratch/.sflo/04-autonomy-environments/qa-model-node-followup.md), [serving assessment](../../.scratch/.sflo/04-autonomy-environments/qa-serving-profile.md).

## Approved documentation — first slice accepted

Candidate **2049361**, 2026-10-02. Exact approved public documentation is fetched under fixed limits, extracted offline, stored with hashes and used for a tool-free local answer with checked span citations. Saved answers replay without network or inference. This does not implement search or browsing.

The complete gate passed **119 tests,86% branch-aware coverage**. Independent functional QA passed. Independent security found two publication/recovery defects in the initial candidate; repaired code passed27 independent fault probes. Actual rig cancellation/owner-death checks left no reusable partial records or containers; explicit cleanup recovered the private store.

On the5090 at96K/Q4, the first frozen question received complete, source-supported JSON separator rules in30.996s. The unsupported future release-date question correctly received insufficient evidence in14.849s. Each used one call, about10.1K prompt tokens, and the existing2048-output-token/120s limits. Independent semantic QA verified every claim, including an extra Python3.4 fact. Both saved answers replayed in a network-none container with unchanged record hashes.

This is two questions against one historical official page, not general research reliability. Citation matching proves provenance; semantic support needs separate assessment. The full Stage4 ten-question/five-browser-journey gate remains pending.

[Usage](../document-evidence.md), [semantic QA](../../.scratch/.sflo/05-autonomy-documents/qa-rig-documents.md), [security recheck](../../.scratch/.sflo/05-autonomy-documents/security-documents-recheck.md), [raw trial](../../.scratch/.sflo/05-autonomy-documents/rig-trial/receipt.json).

### Broader documentation extension — incomplete

Eight additional questions were frozen before further inference. Three answers were saved, one was rejected for changing a quoted curly apostrophe to ASCII, and four asyncio questions never reached inference after source acquisition failed. A separate actual diagnostic reproduced the extractor's10,000-event ceiling on the ordinary official asyncio page.

Independent QA found all three saved answers address their actual questions. One frozen expected-facts list also demanded an unasked return-value fact; this oracle overconstraint is preserved separately from model quality. The original two accepted answers remain unchanged. The larger research gate is unaccepted; [full assessment](../../.scratch/.sflo/05-autonomy-documents/qa-research-cohort.md) and [next reliability work](../../.scratch/autonomy/issues/07-document-reliability.md) retain failures and proposed experiments.

## Supervised local browser — accepted

Source **596ecb6**,2026-10-04. Five stock-reservation flows passed on MONSTER-GAMING-PC: create/reload, validation/recovery, edit/cancel, conflicting sessions and failed-save retry. Five targeted mutants failed the relevant journey assertions. Combined27.649s; screenshots and both conflict-session traces independently checked. Fifteen supplemental controls, startup cancellation and owner death during startup/artifact capture passed. Resource/mount/renderer readbacks and7.0–13.1MB sampled private shared-memory use were observed. Controlled oversized/corrupt artifact and daemon-failure seams are identified separately from actual browser/process tests.

Independent reviews found and repaired origin, cancellation, logging, creation-uncertainty, permissions and seed-atime defects. The first rig failure and later test-harness dispatch error remain preserved; unfinished tests were continued without rerunning passed cases. Full regression gate before the last two narrow repairs:144tests/86%; final seed change:31affected tests pass. Complete29-file runtime and offline browser support are installed, with state/config retained.

This qualifies a supervised verifier for frozen Node apps, not generated web-app quality, public browsing, automatic tool delegation or fullStage4. [Acceptance and evidence](../../.scratch/.sflo/06-autonomy-browser/acceptance.md), [usage](../local-browser.md).
