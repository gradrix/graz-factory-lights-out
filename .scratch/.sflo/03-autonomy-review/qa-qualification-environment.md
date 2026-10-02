# Qualification environment slice QA — PASS

Frozen candidate `4a552b6418220c92b33e5b1f22655293b3354702`; scope only `ops/qualify_coding.py` and `tests/test_qualification.py`. Tests imported reconstructed pinned source, independently of the moving checkout.

| Check | Result |
|---|---|
| Cohort D actual image/version/implementation | Real Docker fb1118 reports 3.12.13 / CPython and matches D manifest |
| Wrong version | main returns 2; persisted environment.json contains actual facts and mismatch; Factory and ModelWorker never constructed |
| Missing image | Real nonexistent pinned image fails closed before Factory/ModelWorker; failure receipt persisted; no state database created |
| Malformed runtime output | Invalid JSON, list, and incomplete facts each reject |
| Legacy unbound cohort | Records actual interpreter facts and expected=null |
| Existing qualification state | Maintained regression rejects before probe/config work and preserves original evidence |
| Focused regression suite | All 3 tests pass |

No defect found in the requested slice. Probe receipts preserve actual execution identity; successful environment matching does not itself qualify model performance. Invalid manifest schema raises before a receipt is written; failure remains closed. This QA does not cover unrelated trajectory serialization or the still-frozen rig experiment.

Reproduce:

```sh
python3 .scratch/.sflo/03-autonomy-review/qa_pinned.py 4a552b6418220c92b33e5b1f22655293b3354702 -m unittest discover -s tests -p test_qualification.py -v
python3 .scratch/.sflo/03-autonomy-review/qa-qualification-environment-probe.py
```

Both exited 0. Evidence: `qa-qualification-environment-tests.log`, `qa-qualification-environment-probe.log`, and complete observed receipts in `qa-qualification-environment-probe.json`. Probe script is saved beside them. No maintained edits, rig changes, model calls, or GPU calls.
