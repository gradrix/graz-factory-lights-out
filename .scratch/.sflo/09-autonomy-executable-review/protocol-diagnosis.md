# Unit09 protocol diagnosis — read-only, cases01–02

Scope: saved local artifacts only. No source, fixture, output or score changes; no rig/model calls. The frozen four-case batch remains authoritative. Recommendations apply only to a separately contracted successor after all four outcomes are preserved.

## Observed failures

| Case | Saved facts | Diagnosis |
| --- | --- | --- |
| case-01 | Five requests, six commands; response05 finish=stop,800 completion tokens. Raw SHA256 `5cdbd1328b9b98a42d3594587906ca60235795052a246efe6e1fb7f50168b12c`. | The final contains fenced JSON followed by prose. Strict json.loads correctly refuses it. The blocking test-cwd finding is supported by command01's11-tests/1-error output and command06's11-pass disposable-copy control, but this does not make the unparseable response an accepted verdict. |
| case-02 | Two requests, two commands; response02 finish=length,4096 completion tokens. Raw SHA256 `ba1f0cd57740c697c8966c63a67d5c56a4cd8a00d2d21ecf96881314687ee294`. | Two proposed tool calls include a truncated5,231-character argument containing a long literal `[` repetition. The whole response was refused before either proposed command ran. This preserves all-or-none validation; no prefix command should be salvaged. |

Artifacts: `.gflo/executable-review-trial-1/{case-01,case-02}/requests/` and `commands/`. Client body construction is `ReviewClient.complete`; protocol dispatch is `review_case` in frozen `ops/executable_review_prototype.py`. The request currently always advertises tools and has no constrained final-response phase.

## Smallest useful successor

Use two explicit request phases with the **same eight-attempt ledger and300-second case deadline**:

1. **Explore with tools.** Reserve one remaining completion slot for finalization. Permit at most one protocol-feedback recovery per case, eligible only for a returned assistant tool response that is truncated or has malformed run arguments. Validate every proposed call before executing any. Store the full failed response, execute none, and add a short controller message stating that no commands ran, the actual remaining budgets, and a request for one compact valid call. Generate large/repeated test data programmatically. Do not insert malformed tool-call messages into API history or fabricate tool results.
2. **Finalize without tools.** On a no-tool exploratory response, tool/request capacity boundary, or an explicit time cutoff, make one separately charged call with tools omitted and `response_format={"type":"json_object"}`. Supply the original objective/source and the valid accumulated tool evidence; any exploratory conclusion remains untrusted data. Apply unchanged `review.validate`, source identity, at-least-one-attested-command and final publication gates. Invalid/truncated finalization is incomplete; do not parse Markdown/prose or add another format-repair call.

A deterministic transition should leave a defined finalization allowance inside300seconds: for example, stop exploration at180seconds, leaving at most120seconds for finalization. Shorten every exploratory HTTP/tool timeout to that phase deadline, not merely the overall deadline. This reduces exploration time and is an explicit tradeoff to freeze, not a free extra allowance. A request-count reserve alone cannot ensure finalization has wall time left. Zero executed commands remains incomplete even if a constrained JSON reply could be obtained.

Use the existing JSON-object mode already employed by `gflo.review.complete`; field/grounding validation remains controller-owned. This avoids introducing an unverified strict-JSON-schema serving feature. Constrained JSON alone does not establish truthful findings or adequate evidence.

### Alternatives

- Adding JSON-object mode to every tools-enabled request is smaller code, but mixes tool and final response modes without a demonstrated serving contract; do not assume it solves both failures.
- A conditional format-repair call only after malformed final prose costs less on already valid finals, but makes finalization optional and evidence less comparable. It still needs the same explicit charged budget and terminal failure rules.
- Stripping fences/extracting an embedded object is not recommended: it silently accepts a protocol the original contract deliberately rejected and invites ambiguous multiple objects or contradictory trailing text.

## Required successor contract changes and controls

The present contract explicitly makes malformed output incomplete without silent retries. Authorize the single narrowly classified feedback recovery, reserved finalization request/time, JSON-only final phase and concise programmatic-data guidance **before** running a new batch. Keep8requests,12commands,300work/150cleanup,4096output/1024thinking and all authority boundaries unchanged. Transport failure, missing start/cleanup evidence, unknown tool authority, changed source and cancellation remain terminal, without recovery. Label repeated known cases as a new protocol experiment; do not rescore these failures or call them fresh qualification.

Controlled gates should prove: fenced exploratory prose leads to a separately debited constrained request; ninth transport is denied; truncated multi-call output executes zero commands; only one eligible feedback event is allowed; finalization cannot dispatch tools; malformed final JSON remains incomplete; absent command evidence fails; shortened phase deadlines preserve the outer deadline; no publication follows cancellation. Preserve raw bodies for both phases and phase labels in the ledger. Root/independent reviewers must still assess evidence truth and the expected defect/control classification.

One semantic caution already visible: case01's trailing prose broadly claims verification of many invalid-input cases, while the six saved commands do not establish that whole list. Its piped unittest command also exits0 because of `tail`, despite clearly failed test output. A successor must not equate exit0 or JSON validity with sufficient semantic evidence. This observation does not alter the current incomplete outcome.

## Reporting precision

Security noted that the current feedback code slices16,384 raw bytes then decodes with replacement. It bounds feedback to at most16,384 characters, potentially49,152 UTF-8 bytes after replacement; the contract only requires bounded output. Clarify that distinction in successor metadata/reporting rather than claiming an exact16KiB encoded-text ceiling. No live mechanism or frozen manifest was changed here.
