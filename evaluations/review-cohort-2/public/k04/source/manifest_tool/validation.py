import re

_PATH_SEGMENT_RE = re.compile(r"\A[A-Za-z0-9_.-]+\Z")
_HEX_LOWER = set("0123456789abcdef")

def entries(value):
    """Validate one manifest list per A1 and return a new list of copied entries.

    Raises ValueError on any invalid input; never mutates the input.
    """
    if not isinstance(value, list):
        raise ValueError("manifest must be a list")
    if len(value) > 100:
        raise ValueError("manifest has more than 100 entries")
    seen = set()
    result = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "size", "sha256"}:
            raise ValueError("entry must have exactly the keys path, size, sha256")
        path = item["path"]
        if not isinstance(path, str):
            raise ValueError("path must be a string")
        if not 1 <= len(path) <= 120:
            raise ValueError("path must be 1..120 characters")
        if not path.isascii():
            raise ValueError("path must be ASCII")
        if "\\" in path:
            raise ValueError("path must not contain a backslash")
        if path.startswith("/"):
            raise ValueError("path must not be absolute")
        if path.endswith("/"):
            raise ValueError("path must not end with a slash")
        if "//" in path:
            raise ValueError("path must not contain repeated slashes")
        for segment in path.split("/"):
            if segment == "." or segment == "..":
                raise ValueError("path segments . and .. are not allowed")
            if not _PATH_SEGMENT_RE.match(segment):
                raise ValueError("path segment must match [A-Za-z0-9_.-]+")
        size = item["size"]
        if isinstance(size, bool) or not isinstance(size, int):
            raise ValueError("size must be an int, not bool")
        if not 0 <= size <= 1000000:
            raise ValueError("size must be 0..1000000")
        sha = item["sha256"]
        if not isinstance(sha, str):
            raise ValueError("sha256 must be a string")
        if len(sha) != 64 or not all(c in _HEX_LOWER for c in sha):
            raise ValueError("sha256 must be exactly 64 lowercase hex characters")
        if path in seen:
            raise ValueError("duplicate path in manifest")
        seen.add(path)
        result.append({"path": path, "size": size, "sha256": sha})
    return result
