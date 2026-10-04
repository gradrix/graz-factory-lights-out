from .validation import entries

def totals(before, after):
    """Byte summary for two manifests (validated via entries(); never mutated).

    Returns exactly {before_bytes, after_bytes, delta_bytes} where delta_bytes
    is after_bytes - before_bytes, summing ALL entry sizes of each manifest.
    """
    before_bytes = sum(e["size"] for e in entries(before))
    after_bytes = sum(e["size"] for e in entries(after))
    return {"before_bytes": before_bytes, "after_bytes": after_bytes, "delta_bytes": after_bytes - before_bytes}
