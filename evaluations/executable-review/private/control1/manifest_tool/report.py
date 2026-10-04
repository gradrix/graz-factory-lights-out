"""Byte totals for validated manifests (requirement A4)."""
from .validation import entries


def totals(before, after):
    """Sum ALL entry sizes of each manifest; delta = after - before.

    Entries must already be validated; validation is idempotent for
    valid input and never mutates the inputs.
    """
    before = entries(before)
    after = entries(after)
    before_bytes = sum(e['size'] for e in before)
    after_bytes = sum(e['size'] for e in after)
    return {'before_bytes': before_bytes,
            'after_bytes': after_bytes,
            'delta_bytes': after_bytes - before_bytes}
