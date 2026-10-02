import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from api import read_asset, health
assert health()=={"status":"ok","version":1}
import tempfile
from pathlib import Path
with tempfile.TemporaryDirectory() as d:
    root=Path(d)/'public'; root.mkdir(); other=Path(d)/'public-private'; other.mkdir()
    (root/'ok').write_text('ok'); (other/'secret').write_text('secret')
    assert read_asset(root,'ok')=='ok'
    try: read_asset(root,'../public-private/secret')
    except ValueError: pass
    else: raise AssertionError('outside file exposed')

with tempfile.TemporaryDirectory() as d:
    root=Path(d)/'root'; root.mkdir(); outside=Path(d)/'secret'; outside.write_text('private')
    (root/'link').symlink_to(outside)
    for name in ['link',str(outside)]:
        try: read_asset(root,name)
        except ValueError: pass
        else: raise AssertionError('outside file exposed')


