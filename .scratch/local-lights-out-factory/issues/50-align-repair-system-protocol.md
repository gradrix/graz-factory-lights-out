# Align repair worker system instructions with enforced response protocol

Type: task
Status: resolved

## Diagnosis

A regression through LocalModel.turn confirms the repair profile still receives the
legacy system instruction requiring complete replacement files. Its user instruction
and parser require exact edits for existing files. Ranked alternatives are ambiguity
about newly created drafts and hash-copy failures; first isolate the confirmed system
contradiction. Preserve default worker messages, parser enforcement, budgets and model.

## Validation

Regression command: pytest tests/test_worker.py::test_local_model_repairs_tokenized_draft_against_its_hash
failed because the transmitted system text lacked the repair protocol. Correct only
the repair system message, verify tokenize/generate equality and legacy behavior,
then run a separately recorded same-policy color trial. Preserve prior failures.

## Answer

Confirmed the legacy full-replacement system message in both retained full-file
protocol failures. Added a dedicated repair system message, selected explicitly by
the repair profile for both tokenization and generation. Default messages and parser
checks are unchanged. Red/green LocalModel regression passes.

Fresh same-policy color build accepted, tests in one response, implementation in
four responses across two attempts. One malformed hash remains; this is not proof of
reliable protocol compliance. Eleven tests, independent oracle/fault gates, preservation
of 85 other files and no-call replay pass. All 446 factory tests/25 subtests pass with
Docker enabled; ruff/mypy pass. No new product edits.

[Results](../repair-system-results.json) preserve traces and old/new instructions.
Next investigate controller-bound short edit handles to reduce hash-copy errors while
preserving exact draft/source identity, and address planner source-reference retries.
