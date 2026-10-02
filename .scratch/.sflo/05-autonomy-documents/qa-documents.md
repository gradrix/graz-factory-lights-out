# Document evidence functional QA

**PASS within first-slice functional scope**, frozen candidate manifest SHA256 `fba3e2f5fe14c640818808b32242c617b7a2ed78c3b2fbb332e7080764b6f336` (baseline `410a46277af9beb0643af7bee1544380f5f687fb`, nine changed files). Every listed source hash verified before and after independent probes. Security and live model/rig qualification remain separate; full Stage4 is not accepted.

| Contract path | Independent result |
|---|---|
| Actual CLI acquire→inspect | Approved Python3.12 JSON documentation fetched successfully with no model configuration; restart inspection reproduces exact ID/spans. Evidence ID `7d14074cb598303b590ba8eb8a0b1fd8a65ae26dc7e820540593832bda6d2e3a`; complete HTTP/executor provenance retained. |
| Frozen corpus extraction | Local framed fetch doubles feed actual offline Docker extraction: benign HTML/plain/Unicode facts preserved; scripts/style/comments/template omitted; hostile visible instructions remain inert. Empty/invalid-UTF8/unsupported-type inputs reject without publication. |
| Exact extraction bounds | Actual offline containers accept 128KiB text, depth64, 2048blocks, 10000events; corresponding +1 controls reject without new records. Event controls use 9997/9998 comments plus one three-event paragraph. |
| Answer→restart→replay | Mock client runs through the real bounded child; request has no tools, max2048tokens, medium/512 thinking, 120s/65536-byte response bounds. CLI answer succeeds. New store instance and CLI replay return unchanged saved answer with fetch and ModelWorker construction set to fail if invoked. |
| Provenance/semantic controls | Invented evidence ID/span/excerpt and model-supplied URL reject. Explicit insufficient-evidence structure validates. An unsupported future-date claim with a genuine quote correctly demonstrates that provenance alone does not prove entailment; independent semantic QA must reject it. |
| Tamper | Change evidence body while restoring original file mode: replay rejects. Restore original bytes: same saved answer replays successfully. |
| Actual lifecycle | SIGKILL owner while its actual bridge-network fetch executor runs a private delayed helper: exact container removed, no receipt; explicit cleanup removes stale scratch. Cancel actual offline extraction after local framed fetch: container/scratch removed and no receipt. No external outage was induced. |
| Focused regression | 27 document protocol/store/answer-child tests pass. |

The local live acquisition and corpus executor receipts show pinned Python image, runc, appropriate bridge/none separation, nonroot, read-only mounts/root, 256MiB memory/swap, one CPU, 64 PIDs and bounded tmpfs; no GPU/socket/project credentials mounted. Synthetic fetch records are explicitly labeled and are not represented as actual HTTP observations. No new functional defect found.

## Reproduction/evidence

All scripts and results are in [qa-documents](qa-documents/):

```sh
python3 .scratch/.sflo/05-autonomy-documents/qa-documents/probe.py
python3 .scratch/.sflo/05-autonomy-documents/qa-documents/live.py
python3 .scratch/.sflo/05-autonomy-documents/qa-documents/bounds.py
python3 .scratch/.sflo/05-autonomy-documents/qa-documents/lifecycle.py
python3 -m unittest discover -s tests -p 'test_document*.py' -v
```

`results.json`, `mock-request.json`, `live-result.json`, `bounds-results.json`, `lifecycle-results.json`, associated logs and `tests.log` preserve retrievable observations. Live reproduction performs the approved documentation fetch; all other acquisition inputs are local doubles or delayed private helper copies. No maintained source edits, model calls, rig changes or private trial-answer inspection. This report does not replace the independent security verdict or infer successful source-grounded model behavior from mocked answers.
