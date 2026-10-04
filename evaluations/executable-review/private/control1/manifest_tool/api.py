"""Public API dispatch (requirement A4)."""
import json
import sys
from .domain import compare
from .report import totals


def run(payload):
    """Handle one API payload.

    * {"action": "ping"} -> {"ok": True}
    * {"action": "compare", "before": [...], "after": [...]} ->
      comparison result plus "summary" from report.totals.

    Anything else raises ValueError.
    """
    if not isinstance(payload, dict):
        raise ValueError('payload must be an object')
    action = payload.get('action')
    if action == 'ping':
        if set(payload) != {'action'}:
            raise ValueError('ping payload must only contain action')
        return {'ok': True}
    if action == 'compare':
        if set(payload) != {'action', 'before', 'after'}:
            raise ValueError('compare payload needs exactly action, before, after')
        result = compare(payload['before'], payload['after'])
        result['summary'] = totals(payload['before'], payload['after'])
        return result
    raise ValueError('unknown action')
