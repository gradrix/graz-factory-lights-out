import json
import re

_NAME_RE = re.compile(r'^[a-z][a-z0-9_]{0,31}$')


def _parse(text: str) -> dict:
    if not isinstance(text, str):
        raise ValueError("input must be a string")
    try:
        obj = json.loads(text, object_pairs_hook=_check_dupes)
    except json.JSONDecodeError:
        raise ValueError("malformed JSON")
    if not isinstance(obj, dict):
        raise ValueError("root must be a JSON object")
    return obj


def _check_dupes(pairs):
    seen: set[str] = set()
    for key, _ in pairs:
        if key in seen:
            raise ValueError(f"duplicate JSON key: {key!r}")
        seen.add(key)
    return dict(pairs)


def _validate(obj: dict) -> None:
    for name, prereqs in obj.items():
        if not isinstance(name, str):
            raise ValueError("node names must be strings")
        if not _NAME_RE.match(name):
            raise ValueError(f"invalid node name: {name!r}")
        if not isinstance(prereqs, list):
            raise ValueError(f"prerequisites for {name!r} must be a list")
        seen: set[str] = set()
        for p in prereqs:
            if not isinstance(p, str):
                raise ValueError(f"prerequisite entries must be strings")
            if p not in obj:
                raise ValueError(f"prerequisite {p!r} is not a key")
            if p == name:
                raise ValueError(f"self-dependency: {name!r}")
            if p in seen:
                raise ValueError(f"duplicate prerequisite {p!r} for {name!r}")
            seen.add(p)


def _topo_sort(obj: dict) -> list[str]:
    # Build in-degree map
    in_degree: dict[str, int] = {name: 0 for name in obj}
    # For each node, track which nodes depend on it (reverse adjacency)
    dependents: dict[str, list[str]] = {name: [] for name in obj}

    for name, prereqs in obj.items():
        for p in prereqs:
            in_degree[name] += 1
            dependents[p].append(name)

    # Kahn's algorithm: at each step pick lexicographically smallest available
    available = sorted(n for n in obj if in_degree[n] == 0)
    result: list[str] = []

    while available:
        node = available.pop(0)  # smallest lexicographically
        result.append(node)
        for dep in dependents[node]:
            in_degree[dep] -= 1
            if in_degree[dep] == 0:
                # Insert into available maintaining sorted order
                import bisect
                bisect.insort(available, dep)

    if len(result) != len(obj):
        raise ValueError("cycle detected")

    return result


def run(text: str) -> list[str]:
    obj = _parse(text)
    _validate(obj)
    if not obj:
        return []
    return _topo_sort(obj)
