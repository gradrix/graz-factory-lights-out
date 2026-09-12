import hashlib
import os
import re
import tempfile
from pathlib import Path


def put_blob(root, chunks, limit=67108864):
    if type(limit) is not int or limit < 1:
        raise ValueError('invalid limit')
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=root)
    try:
        digest = hashlib.sha256()
        total = 0
        with os.fdopen(fd, 'wb') as stream:
            for chunk in chunks:
                if not isinstance(chunk, bytes):
                    raise ValueError('bytes required')
                total += len(chunk)
                if total > limit:
                    raise ValueError('upload too large')
                digest.update(chunk)
                stream.write(chunk)
        key = digest.hexdigest()
        os.replace(name, root/key)
        return key
    finally:
        Path(name).unlink(missing_ok=True)


def open_blob(root, digest):
    if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
        raise ValueError('invalid digest')
    return open(Path(root)/digest, 'rb')
