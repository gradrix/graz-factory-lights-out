# Version-sort repair diagnosis — 2026-09-09

The seen failure is repairable by the local model with explicit reasoning and a
4K output reserve: 3/3 runs passed the fixed gates and all 69 supplemental inputs.
This is a diagnostic result on one known task, not fresh held-out qualification.
The original 109/120 campaign score and its two Acceptance findings are unchanged.

## Reproduction and hypothesis tests

The retained final candidate reverses `["1.0.0", "1"]` incorrectly. Each singleton
passes. Replay used `DockerBroker` against the actual retained candidate; the small
reproduction is in `.gflo/evidence/version-sort-diagnosis-v1/reproduce.py`.

Ranked hypotheses were disabled reasoning, insufficient repair localization, and
repeated deterministic bad edits. The existing source already contained a correct
zero-padding comparator but did not use it for sorting. Baseline attempts kept
producing faulty candidates. Human-authored guidance explicitly identifying that
connection helped inconsistently; it is not autonomous task decomposition.

| Output reserve | Baseline | Reasoning | Targeted guidance |
| --- | --- | --- | --- |
| 2,048 tokens | 0/3 accepted | 0/3; all truncated | 2/3 accepted |
| 4,096 tokens | 0/3 accepted | 3/3 accepted | 2/3 accepted |

Each comparison froze plans and rotated treatment order across three repetitions.
Every plan allowed one attempt and one model turn. Source, original gates, total
8K context budget, temperature 0, seed 42, model checkpoint, and graph-enabled vLLM
service stayed fixed. Atom identities differ across repetitions; this is not a
statistical estimate of general success probability. Source-drift checks passed.

Reasoning used its entire 2K reserve before a complete candidate could be parsed.
At 4K it used 3,482, 1,245, and 3,433 completion tokens and took 60.18, 23.81, and
59.36 seconds end to end. The treatment combines reasoning with sufficient output
space; increasing baseline output space alone did not repair the defect.

The two complete comparisons consumed 18 model observations and 324.73 seconds of
cumulative atom time. Server-reported completion usage was 16,524 tokens. Truncated
responses are excluded from validated worker token totals; their reported usage is
retained separately. Full per-run costs and candidate identities are in
[the portable results](version-sort-diagnosis-results.json).

One interrupted 4K run is separately preserved in
`.gflo/evidence/version-sort-comparison-4k-v1/`: one completed baseline and one
interrupted reasoning attempt. Its expired lease was reconciled. Lost in-flight
usage is unknown, so the completed-comparison totals are not total session costs.
The replacement comparison is `version-sort-comparison-4k-v2`, not a rewritten run.

## Independent review

`scripts/review_version_sort.py` checks 69 deterministic inputs including empty
lists, equivalent versions in different orders, repeated values, leading zeros,
large integers beyond floating-point precision, and varied component counts.
Expected results remain outside the candidate container. Both runs of the review
reject the original bad source, accept a separate reference control, and accept
all seven gate-accepted worker repairs. No discrepancy was discovered by these
finite checks. Review receipts and candidate hashes are retained locally and
summarized in the portable results JSON.

## Implemented boundary

`ModelProfile.profile_id = "vllm-python-worker-reasoning-v1"` enables thinking in
both tokenization and generation. The existing default profile and its serialized
shape are unchanged. Reasoning and the final answer share the atom's output reserve;
truncation still fails closed, and reasoning text never becomes a candidate or gate
receipt. Exact requests and raw responses remain in the artifact store.

The profile follows vLLM's [reasoning API](https://docs.vllm.ai/en/stable/features/reasoning_outputs/)
and the model's [thinking-aware chat template](https://huggingface.co/Inferact/Qwen3.8-27B-NVFP4/blob/6128240ebaf4eaa7bad2b3d1c72c37d677c5f462/chat_template.jinja).
Compatibility was checked against the running pinned deployment, rather than
assuming the current documentation describes every detail of that image.

Regression tests first rejected the new profile, then passed after implementation.
They check matched tokenizer/generation settings, profile identity, retained raw
reasoning, and candidate-only parsing. Full CPU suite: 247 passed, 8 optional Docker
checks skipped, and 25 subtests passed. Ruff and mypy passed. Actual Docker was used
for all live gates and supplemental review in these experiments.

## Repeat on another machine

The [input manifest](version-sort-diagnosis-input.json) is version-controlled so the
experiment does not require transferring the old campaign ledger. Configure the
same local model service and broker, then choose new output paths:

```sh
.venv/bin/python scripts/check_version_sort_repair.py --source-manifest .scratch/local-lights-out-factory/version-sort-diagnosis-input.json --output .gflo/evidence/version-sort-new --output-tokens 4096
.venv/bin/python scripts/review_version_sort.py --campaign .gflo/evidence/version-sort-new --output .gflo/evidence/version-sort-new-review
```

## Next boundary

Keep reasoning opt-in. Qualify a preauthorized escalation policy on multiple task
classes before enabling automatic fallback. Bound aggregate attempts and costs,
preserve provenance between baseline failure and replacement work, and keep the
gates unchanged. Strengthen semantic input partitions and run fresh qualification
before the inventory/reservation workload. This diagnosis does not resolve issue 26's
broader qualification requirement or establish large-system capability.
