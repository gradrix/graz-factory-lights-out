# Independent slice QA — repair recheck

**Candidate:** `ab0395b4a011654f22b0b29a4cc7de53c96df909`. **Verdict: PASS for this visibility/lifecycle slice.** Both initial findings are repaired. Product and maintained tests were unchanged by QA. Full local-model qualification remains separate.

| Check | Result | Evidence in `qa-evidence/` |
|---|---|---|
| D1: fresh missing storage | HTTP 200 with `[]`; observer creates no state directory | `fresh-state-recheck.log`, executable command below |
| D2: cancel in startup cleanup | Conforming inactive control passes; active startup now reports cancelled/cancelled, owner false, cancel requested true | `startup_cancel_probe.py`, `startup-cancel-recheck.log` |
| Existing regression + new startup regressions | 31 tests pass in 10.016s | `suite-recheck.log` |
| Real Docker SIGKILL/cancel/recovery | Writable jobs removed and stop writing; each resumes on attempt 2; exactly one accepted transition; cursor reconnect works | `probe.py`, `probe-recheck.log` |
| HTTP safety and honest acceptance | Three runs observed; write methods, hostile host, traversal/private evidence/symlinks rejected; bounded redacted artifact; changed accepted workspace invalidated | Same probe |
| Rendered desktop/mobile | Light desktop, dark 375px mobile, artifact navigation, no overflow, disconnect snapshot and reconnect all pass | `browser_probe.py`, `browser-recheck.log`, PNGs refreshed on this candidate |

The original browser probe logs “Fresh-state probe unexpectedly returned data” because that diagnostic predates the fix; the separate assertion below verifies the exact repaired response rather than interpreting that sentence as a failure.

## Reproduce

From repository root:

```sh
python3 .scratch/.sflo/02-autonomy-visibility/qa-evidence/startup_cancel_probe.py
python3 .scratch/.sflo/02-autonomy-visibility/qa-evidence/probe.py
/tmp/gflo-browser-check/bin/python .scratch/.sflo/02-autonomy-visibility/qa-evidence/browser_probe.py
python3 -m unittest discover -s tests -v
python3 - <<'PY'
import tempfile, threading, urllib.request, json
from pathlib import Path
from gflo.web import server
with tempfile.TemporaryDirectory() as tmp:
    state = Path(tmp) / 'nonexistent'
    http = server(state, 0)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{http.server_port}/api/runs') as response:
            assert response.status == 200
            assert json.load(response) == []
        assert not state.exists()
        print('Fresh missing state: HTTP 200 [], no filesystem creation PASS')
    finally:
        http.shutdown()
        http.server_close()
PY
```

All commands passed. Real Docker used the pinned local Python image, without GPU/model contention. Initial receipt boundaries still apply: daemon outage/host reboot, container creation races and comprehensive accessibility were not tested. Separate rig qualification must establish actual model-driven outcomes and published/deployed identity.
