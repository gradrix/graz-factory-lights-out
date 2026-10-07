"""Strict validation of manifest entries (requirement A1)."""
import re

MAX_ENTRIES = 100
MAX_PATH_LEN = 120
MAX_SIZE = 1000000
SHA_RE = re.compile(r'\A[0-9a-f]{64}\Z')
SEGMENT_RE = re.compile(r'\A[A-Za-z0-9_.-]+\Z')


def _validate_entry(entry):
    """Return a fresh dict copy for one manifest entry, or raise ValueError."""
    if not isinstance(entry, dict):
        raise ValueError('entry must be an object')
    if set(entry) != {'path', 'size', 'sha256'}:
        raise ValueError('entry must have exactly the keys path, size, sha256')
    path = entry['path']
    size = entry['size']
    sha = entry['sha256']
    if not isinstance(path, str) or not isinstance(sha, str):
        raise ValueError('path and sha256 must be strings')
    if not (1 <= len(path) <= MAX_PATH_LEN):
        raise ValueError('path length must be 1..120')
    if any(ord(ch) > 127 for ch in path):
        raise ValueError('path must be ASCII')
    if '\\' in path or path.startswith('/') or path.endswith('/'):
        raise ValueError('path must be relative with no leading/trailing or backslash')
    segments = path.split('/')
    if any(s == '' for s in segments):
        raise ValueError('no repeated slashes')
    for s in segments:
        if s == '.' or s == '..' or not SEGMENT_RE.match(s):
            raise ValueError('invalid path segment')
    if isinstance(size, bool) or not isinstance(size, int):
        raise ValueError('size must be a strict int, not bool')
    if not (0 <= size <= MAX_SIZE):
        raise ValueError('size must be 0..1000000')
    if not SHA_RE.match(sha):
        raise ValueError('sha256 must be exactly 64 lowercase hex characters')
    return {'path': path, 'size': size, 'sha256': sha}


def entries(value):
    """Validate a manifest list; return a new list of copied entries.

    Raises ValueError for anything malformed. Never mutates the input,
    on success or failure.
    """
    if not isinstance(value, list):
        raise ValueError('manifest must be a list')
    if len(value) > MAX_ENTRIES:
        raise ValueError('manifest has at most 100 entries')
    seen = set()
    result = []
    for item in value:
        entry = _validate_entry(item)
        if entry['path'] in seen:
            raise ValueError('paths must be unique within a manifest')
        seen.add(entry['path'])
        result.append(entry)
    return result
