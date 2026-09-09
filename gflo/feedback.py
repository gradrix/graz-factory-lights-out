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


def _json_errors(value: Any) -> str:
    """Surface observed error fields, without interpreting them as gate failures."""
    if not isinstance(value, str) or len(value) > 87384:
        return ""
    try:
        decoded = base64.b64decode(value, validate=True)
        if len(decoded) > 65536:
            return ""
        root = json.loads(decoded)
    except (ValueError, UnicodeError, RecursionError):
        return ""
    pending = [("$", root, 0)]
    found: list[str] = []
    visited = 0
    while pending and visited < 2048 and len(found) < 8:
        path, node, depth = pending.pop()
        visited += 1
        if depth > 16:
            continue
        if isinstance(node, dict):
            for key, child in reversed(list(node.items())[:128]):
                location = path + "[" + json.dumps(key, ensure_ascii=True) + "]"
                if key == "error":
                    found.append(_text(location + ": " + json.dumps(child, ensure_ascii=True), 192))
                else:
                    pending.append((location, child, depth + 1))
        elif isinstance(node, list):
            pending.extend(
                (path + f"[{i}]", node[i], depth + 1) for i in reversed(range(min(len(node), 128)))
            )
    if not found:
        return ""
    return "Observed JSON error fields (may include expected rejections):\n" + _text(
        "\n".join(found), 768
    )


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
            summary = _json_errors(last.get("stdout_base64"))
            if summary:
                lines.append(summary)
            lines.extend(
                [
                    "Command: " + _text(json.dumps(last.get("command")), 512),
                    "Input (stdin):\n" + _text(last.get("stdin", ""), 1024),
                    "Process outcome: " + _text(last.get("outcome"), 128),
                    "Exit code: " + _text(last.get("exit_code"), 128),
                    "Observed stdout:\n" + _output(last.get("stdout_base64"), 1536),
                    "Observed stderr:\n" + _output(last.get("stderr_base64"), 2048),
                ]
            )
        else:
            lines.append("Malformed execution record; inspect retained evidence.")
    else:
        lines.append("No execution result was retained.")
    if observation.get("error") is not None:
        lines.append("Runner error: " + _text(observation["error"], 512))
    return "\n".join(lines)
