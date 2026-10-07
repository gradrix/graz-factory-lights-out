from .validation import entries

def compare(before, after):
    """Compare two manifests (validated first via entries()).

    Returns exactly {added, removed, modified, renamed, unchanged}.
    Rename detection: among paths absent from the opposite manifest only, a
    signature is (size, sha256); it is a rename only when exactly one unmatched
    old path and exactly one unmatched new path share that signature.
    Ambiguous signatures stay additions/removals; shared paths never rename.
    """
    before_entries = entries(before)
    after_entries = entries(after)
    before_map = {e["path"]: (e["size"], e["sha256"]) for e in before_entries}
    after_map = {e["path"]: (e["size"], e["sha256"]) for e in after_entries}
    before_paths = set(before_map)
    after_paths = set(after_map)
    shared = before_paths & after_paths
    unmatched_before = sorted(before_paths - after_paths)
    unmatched_after = sorted(after_paths - before_paths)
    old_by_sig = {}
    for path in unmatched_before:
        old_by_sig.setdefault(before_map[path], []).append(path)
    new_by_sig = {}
    for path in unmatched_after:
        new_by_sig.setdefault(after_map[path], []).append(path)
    renamed = []
    renamed_from = set()
    renamed_to = set()
    for signature, olds in old_by_sig.items():
        news = new_by_sig.get(signature, [])
        if len(olds) == 1 and len(news) == 1:
            renamed.append({"from": olds[0], "to": news[0]})
            renamed_from.add(olds[0])
            renamed_to.add(news[0])
    renamed.sort(key=lambda pair: pair["from"])
    unchanged = sorted(p for p in shared if before_map[p] == after_map[p])
    modified = [
        {"path": p, "before_size": before_map[p][0], "after_size": after_map[p][0]}
        for p in sorted(shared) if before_map[p] != after_map[p]
    ]
    return {
        "added": [p for p in unmatched_after if p not in renamed_to],
        "removed": [p for p in unmatched_before if p not in renamed_from],
        "modified": modified,
        "renamed": renamed,
        "unchanged": unchanged,
    }
