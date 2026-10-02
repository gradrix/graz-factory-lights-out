# Node availability fixture QA

**PASS for proportional pre-exposure fixture review.** Public manifest `68292397b94126e485d7d119f6c2e6a5692d9232ea366665c309e79eb18d84b5`; protected manifest `2ec5da0ddb1c0e60996efa706360f397e3bc3433c45d05a70205ef48be4daf52`. Author confirmed freeze before independent reads/probes. Both manifest identities and every bound file hash verify.

| Check | Result |
|---|---|
| Objective/oracle | Half-open intervals, clipping/union, maximal sorted free gaps, inclusive minimum duration, validate-before-filter, exact JSON output, input immutability and existing total/CLI behavior correspond to the explicit brief. |
| Reference and solvability | Independent offline strict compile and all original protected checks pass from `/different project/source`, including 80 deterministic occupancy-oracle cases. Reference is a small interval sweep using only approved dependencies. |
| Independent valid edges | Duplicate/nested busy ranges with exact minimum, and full numeric-range window at maximum minimum duration pass. |
| Independent invalid edges | Negative wholly-outside interval, missing nested start and fractional busy endpoint reject through API and CLI without mutation. |
| Controls | Pristine starter rejects; reversing otherwise-correct output order rejects the protected oracle. |
| Author evidence reviewed | Baseline reject; two relocated references pass; eight semantic mutants reject; ordinary English ` at ` error control passes while genuine stack-frame mutant rejects. Initial invalid mutant receipt retained separately. These thirteen author outcomes are supplementary, not represented as independently rerun. |

Protected dependency hashes, strict CommonJS, three passing discovered tests, 40-word README and `availability` literal all have public bases. No unsupported error wording/prose token policy observed. Test meaningfulness and actual documented command quality remain semantic-review requirements; finite executable cases are not exhaustive proof. Reference commands use project-relative paths after explicitly entering the project directory, independent of its location.

## Independent reproduction

```sh
python3 .scratch/.sflo/04-autonomy-environments/qa-node-followup-fixture/probe.py
```

[Probe](qa-node-followup-fixture/probe.py), [results](qa-node-followup-fixture/results.json), [log](qa-node-followup-fixture/probe.log). Actual pinned Node22 image `sha256:88f8ba583a884279252779bbe221bf1ff2c61cf236cc973f8ca97676ae6d07f0`; runc/network-none, no pulls, nonroot, read-only inputs/dependencies/root, bounded scratch/memory/CPU/PIDs. Containers removed.

No fixture/product changes, model exposure, GPU or rig calls. No new fixture defect observed. This permits the planned bounded exposure decision within fixture coverage; it does not establish target-model success or Stage3 acceptance. API v2 QA verdict is unchanged.
