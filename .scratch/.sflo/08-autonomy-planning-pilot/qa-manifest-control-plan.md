# Deferred paired manifest checks

Prepared only; no candidate/control execution while timed arms run.

The existing probe remains SHA256 `f065390d9ec1c833565ce7847f9089082e618b66fdbbfd98416ab35203b740f8`. Control preparer `qa-manifest-controls.py` SHA256 `0b99d4d14bf1a2045b2e1c34ff1053644dd907ea23dcc0396a349109f34085af` has received an AST syntax check only. It refuses existing outputs, copies source without importing it, checks source hashes afterward, and emits complete original/control content hashes.

## Contract correspondence

A6 requires meaningful passing tests discoverable from project root, working unittest commands and a concrete JSON request/response example. Arm1's exact README project-root command is checked at actual `/candidate` cwd; this does not invent arbitrary-cwd test support. A5 separately requires application CLI arbitrary-cwd behavior. Arm2's literal compare payload and expected response are checked after substituting only the executable location, isolating the short-digest error. Literal `/workspace` documentation alone is not a new rejection criterion. Bounds and rename probes derive directly from A1–A3.

## Controlled comparison after coordinator signal

1. Prepare fresh disposable copies using `python3 qa-manifest-controls.py --arm 1 --source ORIGINAL1 --output FRESH/control1` and corresponding `--arm 2` invocation. Originals are never modified.
2. Arm1 control changes only the generated CLI test helper: use `sys.executable`, absolute main.py derived from the test's path, and `/tmp` cwd. All test assertions and implementation remain unchanged.
3. Arm2 control changes only the four malformed README digest literals to64 repeated characters, preserving signature relationships, sizes, paths and the exact documented expected result. Implementation/tests remain unchanged.
4. Run the **same unchanged** probe against each original and each control in fresh pinned Python3.12.13 image `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`, explicit runc/no-pull/network-none/read-only/nonroot, capability drop/no-new-privileges, bounded resources and tmpfs. Mount candidate read-only `/candidate`, probe read-only `/probe`, cwd `/candidate`, `PYTHONDONTWRITEBYTECODE=1`, no `/workspace`. Invoke `python /probe/qa-manifest-probes.py --arm N`.
5. Preserve JSON/stdout/stderr/exit status and container facts for all four runs, including original expected failures. Require boundary/algorithm/CLI checks to pass for both. Expected discrimination: arm1 original unittest fails/control passes; arm2 original README payload fails/control passes. A surprising outcome stays unresolved instead of being forced into a pass.

These synthetic controls establish causal diagnosis only. Their success never changes historical Factory acceptance or independently rescored quality of the untouched generated candidates. No model feedback and no fixes to actual trial trees.
