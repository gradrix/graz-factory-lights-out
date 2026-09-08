"""Bounded, readable projection of retained validation observations for repair."""

from __future__ import annotations

import base64
import binascii
import json
import unicodedata
from typing import Any


def _text(value: Any, limit: int) -> str:
    text = str(value)
    # Bound work before escaping; each escaped character has bounded expansion.
    clipped = text[:limit]
    cleaned = "".join(
        char
        if char in "\n\t" or unicodedata.category(char) not in ("Cc", "Cf")
        else "\\u" + format(ord(char), "04x")
        for char in clipped
    )
    if len(text) > limit or len(cleaned) > limit:
        return cleaned[:limit] + "\n[truncated; full bytes in retained evidence]"
    return cleaned


def _output(value: Any, limit: int) -> str:
    if not isinstance(value, str):
        return "[malformed encoded output; inspect retained evidence]"
    # The broker caps combined output at 1 MiB. Do not decode an oversized report.
    if len(value) > 1_398_104:
        return "[oversized encoded output; inspect retained evidence]"
    try:
        data = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error):
        return "[invalid base64; inspect retained evidence]"
    return _text(data.decode("utf-8", errors="backslashreplace"), limit)


def validation_feedback(observation: dict[str, Any]) -> str:
    """Describe the last executed case; gate expected outputs remain private."""
    lines = [
        "Validation did not pass.",
        "Gate: " + _text(observation.get("gate_id"), 128),
        "Outcome: " + _text(observation.get("outcome"), 128),
    ]
    executions = observation.get("executions")
    if isinstance(executions, list) and executions:
        last = executions[-1]
        lines.append(f"Last executed case: {len(executions)}")
        if isinstance(last, dict):
            lines.extend(
                [
                    "Command: " + _text(json.dumps(last.get("command")), 512),
                    "Input (stdin):\n" + _text(last.get("stdin", ""), 1024),
                    "Process outcome: " + _text(last.get("outcome"), 128),
                    "Exit code: " + _text(last.get("exit_code"), 128),
                    "Observed stdout:\n" + _output(last.get("stdout_base64"), 1536),
                    "Observed stderr:\n" + _output(last.get("stderr_base64"), 3072),
                ]
            )
        else:
            lines.append("Malformed execution record; inspect retained evidence.")
    else:
        lines.append("No execution result was retained.")
    if observation.get("error") is not None:
        lines.append("Runner error: " + _text(observation["error"], 512))
    return "\n".join(lines)
