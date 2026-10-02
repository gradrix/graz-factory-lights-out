# Resumed independent slice QA — PASS

Candidate: `002cf415584b4b1e39f24dc9ff564a5b67ed5c76`; generated-test runtime change: `c17821c31af4a711862a399a3bff650fd1691ddb`. HEAD remained unchanged. Tools and Docker 29.4.3 worked; no account limit occurred. Maintained product and tests were untouched.

| Acceptance / probe | Observation | Verdict / evidence |
|---|---|---|
| Generated failure blocks acceptance, then repair/recheck | External check passed; generated test failed; previous failure reached worker; second attempt passed both checks and review | PASS: `qa-resumed-probe.log`, `qa-resumed-trx04c52/generated-repair/0e0c54f856a7/attempts/` |
| Frozen external checks remain necessary | External failure with generated green exhausted two attempts; reviewer never called. Empty external check list rejected at creation | PASS: same probe, external-failure fixture |
| Clean control | Both checks plus review accepted on attempt 1 | PASS: same probe, clean fixture |
| Generated suite import failure | Exhausted two attempts, no review or acceptance | PASS: same probe, generated-import-error fixture |
| Durable acceptance evidence | Unchanged accepted run resumed accepted; altering verification receipt invalidated acceptance in both accepted controls | PASS: same probe assertions |
| Sandbox isolation/lifecycle | All 5 real Docker tests passed, including read-only verification and killed-owner cleanup | PASS: `qa-resumed-sandbox.log` |
| Controller lifecycle and review regressions | 13 runner and 14 review tests passed | PASS: `qa-resumed-runner.log`, `qa-resumed-review.log` |
| Model qualification and held-out task cohort | No model/GPU calls; 10+10 comparison, critical-seed recall, switching overhead, and 10/12 held-out outcomes not newly evaluated | NOT COVERED; no final Stage 2 acceptance |

No defect found in this slice. Generated unittest failures supplement the frozen external checks and reach the controller repair loop. The independent negative control establishes that a passing generated suite cannot override failed external acceptance. Review and worker responses in the new controller probe are deterministic callbacks; the verification commands execute in real Docker. This evidence does not establish model semantic accuracy or completeness of generated tests. Discovery uses the configured Python unittest `tests` convention.

## Reproduction

From `/home/gradrix/repos/gflo`:

```sh
python3 .scratch/.sflo/03-autonomy-review/qa-resumed-probe.py
python3 .scratch/.sflo/03-autonomy-review/qa_pinned.py 002cf415584b4b1e39f24dc9ff564a5b67ed5c76 -m unittest discover -s tests -p test_sandbox.py -v
python3 .scratch/.sflo/03-autonomy-review/qa_pinned.py 002cf415584b4b1e39f24dc9ff564a5b67ed5c76 -m unittest discover -s tests -p test_runner.py -v
python3 .scratch/.sflo/03-autonomy-review/qa_pinned.py 002cf415584b4b1e39f24dc9ff564a5b67ed5c76 -m unittest discover -s tests -p test_review.py -v
```

All four checks exited 0. Regression suites were originally executed from the unchanged checkout; the commands above reconstruct the same candidate for repeatability. The independent probe always reconstructs the pinned candidate and creates a new scratch evidence directory. Original durable evidence is in `qa-resumed-trx04c52/results.json` and its run directories. In accepted controls, final verification receipts are deliberately replaced with `{}` to test invalidation; preceding probe assertions establish acceptance before that mutation.
