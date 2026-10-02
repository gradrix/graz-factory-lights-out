# Final targeted lifecycle QA

**Candidate:** `89a17ad206ce976ab958c13e29276bb3aa3ddb4a`. **Verdict: repair required** for one command argument regression introduced by guardian changes.

| Check | Result | Evidence |
|---|---|---|
| Real Docker sandbox suite | 3 tests pass, including closed owner pipe never starting a writer | `qa-evidence/sandbox-final.log` |
| Independent live writer SIGKILL/cancel/recovery | Both stop writes, remove container, report honest state, resume at attempt 2, accept exactly once | `qa-evidence/probe-final.log`, executable `probe.py` |
| HTTP boundaries / changed accepted workspace | Repeated independent probe passes | Same probe |
| User argument preservation | `--keep` control preserved; `--rm` silently removed from Python command, causing IndexError | **D3:** `qa-evidence/argv-final.log` |

**D3:** `gflo/guard.py` removes every `--rm` token from the complete Docker command while converting run to create. That includes the worker's program arguments after the image. Remove only the Docker option, preserving the requested command exactly.

Reproduction (real pinned Docker; exit 1 demonstrates regression after passing control):

```sh
python3 - <<'PY'
import tempfile
from gflo.sandbox import Sandbox
with tempfile.TemporaryDirectory() as workspace:
    for argument in ('--keep', '--rm'):
        result = Sandbox().execute(workspace, [
            'python', '-c', 'import sys; assert sys.argv[1] == ' + repr(argument), argument])
        print(argument, result, flush=True)
        assert result['exit_code'] == 0
PY
```

Other commands:

```sh
python3 -m unittest discover -s tests -p test_sandbox.py -v
python3 .scratch/.sflo/02-autonomy-visibility/qa-evidence/probe.py
```

Unchanged HTTP/browser acceptance evidence remains bound to `ab0395b4a011654f22b0b29a4cc7de53c96df909` in `qa-recheck.md`. No product or maintained test edits by QA. Real-model rig outcomes are independently owned by the rig qualification receipt; this check does not certify their deployment. Docker daemon outage, host reboot and general accessibility remain outside coverage.
