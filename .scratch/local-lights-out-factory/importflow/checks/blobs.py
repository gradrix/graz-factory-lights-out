import hashlib
import tempfile
import tracemalloc
from pathlib import Path
from unittest.mock import patch
import blobs

with tempfile.TemporaryDirectory() as folder:
    root=Path(folder)/'blobs'
    key=blobs.put_blob(root,[b'abc',b'def'])
    assert key==hashlib.sha256(b'abcdef').hexdigest(), 'content digest'
    assert blobs.put_blob(root,[b'abcdef'])==key
    with blobs.open_blob(root,key) as stream:
        assert stream.read()==b'abcdef'
    for bad in ('../bad','a'*64+'\n','A'*64,'f'*63):
        try: blobs.open_blob(root,bad)
        except ValueError: pass
        else: raise AssertionError(('invalid digest accepted',repr(bad)))
    for chunks,limit in (([b'abcd'],3),(['text'],100),([b'ok'],True),([b'ok'],0)):
        try: blobs.put_blob(root,chunks,limit=limit)
        except ValueError: pass
        else: raise AssertionError(('invalid payload accepted',chunks,limit))
        assert sorted(p.name for p in root.iterdir())==[key], 'temporary leak'
    def broken():
        yield b'first'
        raise OSError('injected producer failure')
    try: blobs.put_blob(root,broken())
    except OSError: pass
    else: raise AssertionError('producer failure swallowed')
    with patch('os.replace',side_effect=OSError('injected replace failure')):
        try: blobs.put_blob(root,[b'abcdef'])
        except OSError: pass
        else: raise AssertionError('replace failure swallowed')
    assert sorted(p.name for p in root.iterdir())==[key]
    assert (root/key).read_bytes()==b'abcdef'
    tracemalloc.start()
    large=blobs.put_blob(root,(b'x'*65536 for _ in range(64)))
    _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    assert peak<1*1024*1024, ('whole payload buffered',peak)
    assert (root/large).stat().st_size==4*1024*1024
print('blobs-ok')
