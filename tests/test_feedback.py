"""Projection tests: actionable failures, bounded untrusted bytes, private expectations."""

import base64

import pytest

from gflo.feedback import validation_feedback


def execution(**changes):
    return {
        "command": ["python", "main.py"],
        "stdin": '""\n',
        "outcome": "completed",
        "exit_code": 1,
        "stdout_base64": "",
        "stderr_base64": base64.b64encode(
            b"AttributeError: 'str' object has no attribute 'get'\n"
        ).decode(),
    } | changes


def test_last_failing_case_is_readable_without_gate_answers():
    result = validation_feedback(
        {
            "gate_id": "behavior",
            "outcome": "fail",
            "executions": [execution(stderr_base64="", exit_code=0), execution()],
            "expected_stdout": "PRIVATE ANSWER",
            "plan": {"secret": "PRIVATE PLAN"},
        }
    )
    assert "Last executed case: 2" in result
    assert "AttributeError: 'str' object has no attribute 'get'" in result
    assert 'Input (stdin):\n""\n' in result
    assert "PRIVATE" not in result and "stderr_base64" not in result


@pytest.mark.parametrize(
    "encoded, expected",
    [
        ("not-base64", "invalid base64"),
        (None, "malformed encoded output"),
        (base64.b64encode(b"\xff\x1b[2J").decode(), "\\xff\\u001b[2J"),
        ("x" * 1398105, "oversized encoded output"),
    ],
)
def test_bad_bytes_are_visible_without_masking_failure(encoded, expected):
    text = validation_feedback({"executions": [execution(stderr_base64=encoded)]})
    assert expected in text
    assert "\x1b" not in text


def test_all_fields_and_control_expansion_stay_within_diagnostic_budget():
    huge = "\x1b" * 20000
    encoded = base64.b64encode(huge.encode()).decode()
    text = validation_feedback(
        {
            "gate_id": huge,
            "outcome": huge,
            "error": huge,
            "executions": [
                execution(
                    command=[huge] * 64,
                    stdin=huge,
                    outcome=huge,
                    exit_code=huge,
                    stdout_base64=encoded,
                    stderr_base64=encoded,
                )
            ],
        }
    )
    assert len(text) <= 8192
    assert "[truncated;" in text and "\x1b" not in text


@pytest.mark.parametrize("executions", [None, [], [None]])
def test_inconclusive_malformed_report_still_has_feedback(executions):
    text = validation_feedback(
        {"outcome": "inconclusive", "executions": executions, "error": "bad identity"}
    )
    assert "inconclusive" in text and "bad identity" in text


def test_late_workflow_error_visible_before_truncated_output():
    import json

    output = {"padding": "x" * 3000, "responses": [{"ok": True}] * 12 + [{"error": "invalid"}]}
    result = validation_feedback(
        {
            "executions": [
                execution(
                    stdout_base64=base64.b64encode(json.dumps(output).encode()).decode(),
                    stderr_base64="",
                    exit_code=0,
                )
            ]
        }
    )
    assert '$["responses"][12]["error"]: "invalid"' in result
    assert result.index("Observed JSON error fields") < result.index("Observed stdout:")


@pytest.mark.parametrize("raw", [b"[" * 2000 + b"]" * 2000, b"{bad", b"\xff"])
def test_error_summary_ignores_unparseable_json(raw):
    result = validation_feedback(
        {"executions": [execution(stdout_base64=base64.b64encode(raw).decode(), stderr_base64="")]}
    )
    assert "Observed JSON error fields" not in result


def test_json_error_summary_is_bounded_and_does_not_claim_gate_mismatch():
    import json

    raw = json.dumps([{"error": "\x1b" * 100}] * 8).encode()
    result = validation_feedback(
        {"executions": [execution(stdout_base64=base64.b64encode(raw).decode(), stderr_base64="")]}
    )
    assert "may include expected rejections" in result
    assert len(result) <= 8192
    assert "\x1b" not in result
