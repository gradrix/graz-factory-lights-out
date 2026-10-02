# Generated Node availability semantic QA

**PASS for this generated candidate**, run `df7b986b2ae8`, candidate fingerprint `e5dce45defd92613a7a288f33e268c7f8eb182e23f831a4fa9b74f9a4fecffda`, patch SHA256 `ec77bc16797c04b2aea516c7dca314bf65b1e8ed1d8f54fc051cc2b163bab9b5`. Workspace fingerprint, patch and accepted verification/review hashes match frozen evidence. No new semantic defect found.

| Scope | Independent observation |
|---|---|
| Implementation | Validates every interval before filtering; clips into new objects; sorts and merges adjacency/overlap without modifying callers; returns maximal sorted gaps meeting the inclusive duration threshold. Type/range checks and existing total behavior are retained. |
| Beyond-oracle results | 150 deterministic random cases match an independent discrete free-cell grouping calculation. Ten also pass through the real CLI from unrelated working directory. |
| Immutability/rejection | All valid random inputs recursively frozen and compared afterward. Seven further frozen invalid cases reject unchanged: negative outside interval, upper overflow, fraction, missing endpoint, NaN, Infinity and sparse interval array. |
| Generated tests | Three meaningful node:test cases pass both the documented explicit test path and automatic `node --test` discovery. They cover overlap/clip/order, exact minimum/full/empty boundaries and multiple rejection classes. Their single-field mutation assertion is limited; independent deep-freeze checks supply stronger coverage. |
| README commands | Exact documented offline compiler, test and echo-to-CLI commands pass in a relocated project directory containing a space. Example produces the two correct free gaps. Documentation explicitly requires the project-root working directory, independent of project location. |
| Repair provenance | Attempt1 worker receipt records empty summary, two turns/two tool calls and stop; external verification rejects unknown availability action. Attempt2 acceptance is bound to passing checks and review. This is observed check→repair→recheck, not evidence that reviewer criticism caused the repair. |

## Reproduction

```sh
python3 .scratch/.sflo/04-autonomy-environments/qa-model-node-followup/probe.py
```

[Host probe](qa-model-node-followup/probe.py), [container probe](qa-model-node-followup/inside.cjs), [results/commands](qa-model-node-followup/results.json), [log](qa-model-node-followup/probe.log). Actual Node v22.23.3 pinned image, prepared locked dependencies, runc/network-none, nonroot and read-only candidate/dependency mounts. Compilation and generated outputs stay in disposable scratch; container removed.

The reported 178.41s model run remains a historical rig measurement in `rig-node-followup.json`; no model calls were made by QA. No generated-candidate edits, rig/GPU calls or broad Stage3 acceptance claim. This closes the requested generated-Node semantic check within stated coverage.
