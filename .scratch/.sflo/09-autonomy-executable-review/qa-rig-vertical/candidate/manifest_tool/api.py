from .domain import compare
from .report import totals

def run(payload):
    """Single API entry point.

    {action: "ping"} -> {ok: True}
    {action: "compare", before: [...], after: [...]} -> compare result plus
    summary = totals(before, after)
    Anything else (unknown action, unknown/missing fields, malformed payload)
    raises ValueError.
    """
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    action = payload.get("action")
    if action == "ping":
        if set(payload) != {"action"}:
            raise ValueError("unexpected fields for ping action")
        return {"ok": True}
    if action == "compare":
        if set(payload) != {"action", "before", "after"}:
            raise ValueError("unexpected or missing fields for compare action")
        result = dict(compare(payload["before"], payload["after"]))
        result["summary"] = totals(payload["before"], payload["after"])
        return result
    raise ValueError("unknown action")
