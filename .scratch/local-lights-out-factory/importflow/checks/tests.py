import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

mutants={
    'empty':('tabular.py','\ndef summarize(*args,**kwargs):\n    return []\n'),
    'duplicate':('jobs.py','\n_saved_submit=Store.submit\ndef _bad_submit(self,key,kind,payload):\n    import uuid\n    return _saved_submit(self,uuid.uuid4().hex,kind,payload)\nStore.submit=_bad_submit\n'),
    'finish':('jobs.py','\nStore.finish=lambda *args,**kwargs:False\n'),
}
for name,item in [('correct',None),*mutants.items()]:
    with tempfile.TemporaryDirectory() as folder:
        dest=pathlib.Path(folder)
        for module in ('blobs.py','tabular.py','jobs.py','worker.py','api.py'):
            shutil.copyfile(module,dest/module)
        shutil.copytree('tests',dest/'tests')
        if item:
            path=dest/item[0];path.write_text(path.read_text()+item[1])
        # Count actual collected cases, including parametrized cases.
        count=subprocess.run([sys.executable,'-m','pytest','--collect-only','-q','-p','no:cacheprovider'],cwd=dest,text=True,capture_output=True)
        cases=[line for line in count.stdout.splitlines() if '::' in line and not line.startswith(' ')]
        assert count.returncode==0 and len(cases)>=8,('need eight collected cases',count.stdout,count.stderr)
        run=subprocess.run([sys.executable,'-m','pytest','-q','-p','no:cacheprovider'],cwd=dest,text=True,capture_output=True,timeout=30)
        assert run.returncode==(0 if name=='correct' else 1),(name,run.returncode,run.stdout,run.stderr)
        assert not any(word in run.stdout for word in ('skipped','xfailed','xpassed')),(name,run.stdout)
print('tests-ok')
