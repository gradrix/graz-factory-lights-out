"""Manifest comparison with rename detection (requirements A2, A3)."""
from .validation import entries


def compare(before, after):
    """Compare two manifests and return added/removed/modified/renamed/unchanged.

    Inputs are validated strictly (see validation.entries) and are never
    mutated, on success or failure.
    """
    before = entries(before)
    after = entries(after)
    before_by_path = {e['path']: e for e in before}
    after_by_path = {e['path']: e for e in after}

    added_paths = sorted(p for p in after_by_path if p not in before_by_path)
    removed_paths = sorted(p for p in before_by_path if p not in after_by_path)

    modified = []
    unchanged = []
    for path in sorted(before_by_path):
        if path not in after_by_path:
            continue
        b = before_by_path[path]
        a = after_by_path[path]
        if b['size'] == a['size'] and b['sha256'] == a['sha256']:
            unchanged.append(path)
        else:
            modified.append({'path': path,
                             'before_size': b['size'],
                             'after_size': a['size']})

    # Rename detection: only unmatched (added/removed) paths participate.
    # Signature (size, sha256) must pair exactly one old and one new path.
    old_sigs = {}
    for p in removed_paths:
        e = before_by_path[p]
        old_sigs.setdefault((e['size'], e['sha256']), []).append(p)
    new_sigs = {}
    for p in added_paths:
        e = after_by_path[p]
        new_sigs.setdefault((e['size'], e['sha256']), []).append(p)

    renamed_pairs = []
    renamed_old = set()
    renamed_new = set()
    for sig, olds in old_sigs.items():
        news = new_sigs.get(sig, [])
        if len(olds) == 1 and len(news) == 1:
            renamed_pairs.append((olds[0], news[0]))
            renamed_old.add(olds[0])
            renamed_new.add(news[0])

    renamed = [{'from': f, 'to': t} for f, t in sorted(renamed_pairs)]
    added = [p for p in added_paths if p not in renamed_new]
    removed = [p for p in removed_paths if p not in renamed_old]

    return {'added': added,
            'removed': removed,
            'modified': modified,
            'renamed': renamed,
            'unchanged': unchanged}
