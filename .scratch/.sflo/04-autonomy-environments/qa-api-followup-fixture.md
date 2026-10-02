# Telemetry API fixture independent QA

**BLOCKED before model exposure: one concrete false-pass gap.** Protected manifest `72a7fd6eca78d476845c07f27ea143e75fbc0581758bd1f20a6e30c3421df193`; public manifest `1accec55480d81d4467e0d6b96b5639ca43deb7444567fa3b7862a997085be34`.

## Finding

The public objective requires sample timestamps to be strict integers in 0..1,000,000,000. Replacing only `Sample.at:BoundedInt` with `Sample.at:StrictInt` in the private reference passes the complete original oracle, including generated tests. It accepts negative timestamps.

Independent discriminating HTTP input: `{"start":0,"end":3,"samples":[{"device":"a","at":-1,"reading":0}]}`. Required result: HTTP422. Add this case at the beginning of the oracle invalid-case list: the conforming reference passes; the mutant rejects at the schema/domain assertion. Repair the protected cases under a new manifest and retain the original fixture. Checking both timestamp bounds is a proportional extension of the same finding.

| Check | Result |
|---|---|
| Identity/integrity | Public, protected, original v2 and corrected v3 manifests match supplied hashes; every manifest-bound file hash verified. |
| Starter | Offline wheel/HTTP oracle fails at missing new endpoint as intended. |
| Reference | Passes relocated source, offline installed wheel, real HTTP, direct-domain immutability, generated tests and independent negative timestamp case. |
| Mutant | Original oracle passes; independent negative timestamp case fails. |
| Objective correspondence | Window/reset/baseline semantics are coherent and reference arithmetic matches the stated transitions. Dependency, exact types, docs minimum/interface literals and test-count assertions have explicit public bases. Semantic test/docs quality remains an independent review obligation. |
| V3 provenance | Original v2 manifest `858384ee7ca74724efe1ee4247c69cc039d88e8b53b344ef42c5f6c6d6e9989b` remains intact. Corrected v3 `ff1ebb8b8846dcef0006f63f4afc5ff1149c941df8f4c130af098e06a6299d08` changes the API oracle by exactly removing ` and 'pip' in doc`. This is a fixture correction, not a rescore of the earlier timeout or incorrect Uvicorn target. |

## Evidence and boundaries

[Probe](qa-api-followup-fixture/probe.py), [results](qa-api-followup-fixture/results.json), [log](qa-api-followup-fixture/probe.log).

```sh
python3 .scratch/.sflo/04-autonomy-environments/qa-api-followup-fixture/probe.py
```

Actual pinned Python3.12.13, runc/network-none, nonroot, bounded scratch/memory/PIDs and read-only project/dependency/oracle binds. Each container removed. Initial probe appended its new case, inadvertently changing the existing `invalid[-1]` direct-duplicate control; preserved as `harness-initial-results.json`, then corrected by inserting at index0. Final four outcomes are baseline fail, conforming reference pass, mutant original pass, mutant augmented reject.

No protected fixture/runtime changes, models, GPU or rig calls. This proportional review does not exhaust all schema combinations or certify eventual model solvability within budget. Builder notified to create a versioned repair; no Stage3 acceptance claim.

## Recheck: repaired protected v2

**PASS for the concrete fixture finding** on protected manifest `e4cdd35d290c86aa115ae1c7e76d87acfdc5be135e6779768e0f7a0c646f9a5e`. Original blocked verdict above remains bound to v1.

Independent offline recheck: unchanged conforming reference passes the full v2 oracle, including timestamp zero/max boundary controls; exact `Sample.at:BoundedInt` → `Sample.at:StrictInt` mutant now fails `schema/domain rejection`. Added negative/upper timestamp, negative start and upper reading cases follow existing public bounds, with no new policy. The final duplicate case remains intact for the direct rejection/immutability check. Task and reference are byte-identical to v1. All v2 bound hashes verify; original v1, public, original qualification v2 and corrected qualification v3 identities still verify unchanged.

Evidence: [v2 probe](qa-api-followup-fixture/recheck-v2.py), [two results](qa-api-followup-fixture/v2-results.json), [log](qa-api-followup-fixture/v2.log). Reproduce with `python3 .scratch/.sflo/04-autonomy-environments/qa-api-followup-fixture/recheck-v2.py`. Actual pinned Python3.12.13/runc offline containers; no model exposure or maintained changes. This closes the identified pre-exposure fixture blocker within proportional coverage, not Stage3 acceptance or exhaustive oracle completeness.
