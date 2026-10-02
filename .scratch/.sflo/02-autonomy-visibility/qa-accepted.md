# Independent QA acceptance

**Final candidate:** `18a274fa2e1391f744feb8d06f8eda17157ab27f`. **Verdict: PASS for the visibility/lifecycle slice.** No outstanding confirmed defects from this review. QA changed no maintained product/tests.

| Evidence scope | Candidate | Result |
|---|---|---|
| D3 independent real-Docker argument preservation | `18a274fa2e1391f744feb8d06f8eda17157ab27f` | `--keep` control and formerly failing `--rm` both preserved; command exits 0 (`qa-evidence/argv-accepted.log`) |
| Guardian closed-owner startup and active writer kill/cancel/recovery | `89a17ad206ce976ab958c13e29276bb3aa3ddb4a` | Three sandbox tests and independent lifecycle probe pass (`qa-final.md`); final change only preserves argv and validates internal prefix |
| D1 fresh observer and D2 startup cancellation | `ab0395b4a011654f22b0b29a4cc7de53c96df909` | Both repaired and independently reproduced as passing (`qa-recheck.md`) |
| Read-only API, paths, bounded/redacted evidence, accepted-artifact honesty | `ab0395b`, repeated at `89a17ad` | Independent probes pass; affected code unchanged since evidence |
| Rendered desktop/mobile, artifact navigation, disconnect/reconnect | `ab0395b4a011654f22b0b29a4cc7de53c96df909` | Browser assertions and screenshots pass; UI/API unchanged |
| Full regression at visibility fix | `ab0395b4a011654f22b0b29a4cc7de53c96df909` | 31 tests pass; subsequent guardian regression evidence is scoped above |

Final independent command, from repository root (exit 0):

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

All real-Docker probes use the pinned local Python image and no GPU/model calls. This receipt combines current targeted verification with unaffected prior evidence rather than claiming a fresh full suite on the final hash. Actual local-model three-project trials and deployed rig identity require the separate qualification/deployment receipt. Daemon outage/host reboot and comprehensive accessibility remain outside this review.
