"""Generated tests must reject behavior faults with assertions, not crashes."""

import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

mutants = {
    "filter": "\n_saved_list = list_tasks\ndef list_tasks(path, include_done=False):\n    return _saved_list(path, True)\n",
    "ids": "\n_saved_add = add_task\ndef add_task(path, title):\n    task = _saved_add(path, title)\n    return {**task, 'id': 1}\n",
    "completion": "\n_saved_complete = complete_task\ndef complete_task(path, task_id):\n    from pathlib import Path\n    old = Path(path).read_bytes()\n    result = _saved_complete(path, task_id)\n    Path(path).write_bytes(old)\n    return result\n",
    "title": "\n_saved_add = add_task\ndef add_task(path, title):\n    if isinstance(title, str) and not title.strip():\n        title = 'accepted empty title'\n    return _saved_add(path, title)\n",
}
runner = """import pytest,sys
class Audit:
    bad_exception = False
    def pytest_runtest_makereport(self,item,call):
        if call.excinfo and not issubclass(call.excinfo.type,(AssertionError,pytest.fail.Exception)):
            self.bad_exception = True
plugin = Audit()
code = pytest.main(sys.argv[1:],plugins=[plugin])
sys.exit(99 if plugin.bad_exception else code)
"""
source = Path("taskdock.py")
original = source.read_text()
preserved = {
    p: p.read_bytes() for p in Path(".").rglob("*") if p.is_file() and ".pyc" not in p.name
}
try:
    for name, suffix in [("candidate", ""), *mutants.items()]:
        source.write_text(original + suffix)
        with tempfile.TemporaryDirectory() as folder:
            xml = Path(folder) / "result.xml"
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    runner,
                    "-q",
                    "-p",
                    "no:cacheprovider",
                    "--junitxml=" + str(xml),
                    "tests/test_taskdock.py",
                ],
                capture_output=True,
                text=True,
            )
            assert xml.exists(), (name, result.stdout, result.stderr)
            tree = ET.parse(xml)
            assert len(tree.findall(".//testcase")) >= 6
            assert not tree.findall(".//skipped") and not tree.findall(".//error"), (
                name,
                result.stdout,
            )
            if name == "candidate":
                assert result.returncode == 0, (name, result.stdout, result.stderr)
            else:
                assert result.returncode == 1 and tree.findall(".//failure"), (
                    name,
                    result.stdout,
                    result.stderr,
                )
        assert source.read_text() == original + suffix, "tests changed implementation"
        assert all(p == source or p.read_bytes() == content for p, content in preserved.items())
finally:
    source.write_text(original)
print("tests-ok")
