# Task-created draft repair qualification

The windows worker distinguishes immutable input paths from task-created draft paths.
The host verifies the base against the contract input digest. Full candidates can replace
new draft files; immutable input files still require exact window edits. Current-draft
identity, write scope and complete-bundle validation remain enforced. No retry increase.

## Results

- Retained test-decomposition-v2 solo-2: original candidate fails; its unedited next
  response previously rejected by the protocol now passes all four fault gates. This
  is response replay, not fresh inference. `retained.py` reproduces it using portable
  responses and the original source fixture. Raw: `.gflo/evidence/draft-repair-retained-v2`.
  The v1 harness stopped before execution because broker qualification was missing;
  it is retained separately and contains no model inference.
- Three fresh solo trials: all accepted, using 1, 2 and 1 model responses respectively.
  Solo-2 exercised complete replacement of its generated draft with fresh local inference.
  Accepted replay left ledger states unchanged. See `results.json` for full responses.
- Same pinned model, GPU deployment, source, fault gates, two attempts and three turns
  per attempt as the earlier decomposition campaign. No manual response correction.
- Full Docker suite: 499 tests and 25 subtests. Ruff and mypy passed. Four historical
  accepted/halted/challenged runs replayed with zero new events.

Run from repository root with `PYTHONPATH=. .venv/bin/python` followed by `campaign.py`
or `retained.py` in this directory. Each refuses an existing evidence directory.
The source fixture and gates are reused from `../test-decomposition/campaign.py`.
Three trials establish a working regression, not a general reliability rate.
