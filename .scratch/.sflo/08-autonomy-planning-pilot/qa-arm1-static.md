# Arm 1 independent static review

**Core implementation appears conforming; one test/documentation portability finding remains for dynamic confirmation.** This is static review only, not final semantic acceptance. No candidate code, tests, Docker or inference executed.

Identity: arm `1-manifest-reconcile-direct`, run `b420f7770b76`. Independently reconstructed names/modes/content fingerprint exactly matches `5dc1f9fd353e215802c8b363f20db41371ae5db99b086601c054a348bb3d918d`. Full immutable evidence is `.gflo/planning-trial-1/1-manifest-reconcile-direct`. Saved receipts record accepted, 321.077 seconds, 23 calls (21 implementation, two code reviews), final verification passed and both reviews passed.

## Finding: generated CLI tests assume the controller mount path

`factory/b420f7770b76/workspace/tests/test_manifest_tool.py`, `CliBehavior._run_cli`, invokes `python main.py` with hardcoded `cwd='/workspace'`. README says to run unittest from the project root and gives `/path/to/project` as an equivalent source location. A checkout elsewhere cannot run this CLI test unless `/workspace` exists; if it does exist, it may execute unrelated code. The actual CLI entrypoint itself uses package-relative imports and appears portable. The issue is the delivered regression test/documented test workflow, not the comparison algorithm.

The model's request 17 tried changing current directory while the project remained mounted at `/workspace`; this could not detect relocation. Both reviews missed the distinction. Confirm after all timed arms finish by mounting a disposable exact copy at `/project` with no `/workspace`, then executing the README command. Do not edit the captured candidate. Suggested repair, if later authorized: derive the project root from the test file and invoke its absolute main.py using `sys.executable`.

## Requirement review

| Requirement | Static assessment |
|---|---|
| A1 strict validation/nonmutation | Bounds, ASCII component restrictions, duplicate paths, exact fields, bool/float rejection and lowercase 64-character digest are implemented. Validation returns copied scalar-entry dictionaries; partial failures do not write input. |
| A2 shared-path classification | Shared paths handled first; both size/hash determine unchanged; deterministic sorted output and empty case are correct. |
| A3 unique unmatched renames | Signature groups built from complete original unmatched sets; only one-to-one groups removed from additions/removals. Shared paths excluded; ambiguous groups retained. |
| A4 totals/API | All sizes included, signed delta correct; exact compare fields and ping retained. Totals redundantly revalidates valid inputs, harmless at the bounded size. |
| A5 CLI | Reads one JSON value; malformed/value/type/recursion errors map to exit 2 and JSON error. Absolute main.py invocation should work from arbitrary cwd. No comparison I/O beyond supplied values. |
| A6 generated tests/docs | Eleven substantive methods cover ordinary classifications, unique/ambiguous rename, shared paths, invalid entries, nonmutation, totals, API and CLI. README explains behavior/errors and supplies a consistent concrete example. Relocated test invocation defect above. |

Tests include real assertions rather than placeholders. The failed-validation nonmutation method catches ValueError without separately requiring it, but the dedicated rejection method does require errors. No consequential filler or unnecessary abstraction found; unused json/sys imports in api.py are cosmetic only. The README statement about touching no files is naturally scoped to application data, not interpreter imports.

## Deferred narrow dynamic checks

After timed arms finish: relocated README unittest command; absolute-path CLI from unrelated cwd; exact valid upper boundaries (100 entries, 120-character path, size 1000000), forbidden newline/non-ASCII path/digest, asymmetric ambiguous signatures and input permutation invariance. These are verifier-chosen risks beyond merely repeating the frozen oracle. Existing saved acceptance and raw tool evidence remain observed historical results, not independently rerun results.

### Precise A6 scope

Evidence lines: generated test `test_manifest_tool.py:175–178`; README `README.md:52–56`. Original frozen A6 explicitly requires tests discoverable from the project root, tests passing offline, working unittest commands, and specifies `python -m unittest discover -s /path/to/project`. It does not separately say that every generated test must support arbitrary caller cwd. The narrow expected behavior is therefore that the advertised project-root command works for the supplied project at its actual path; the absolute `/workspace` dependency contradicts that claim when relocated. A5's explicit arbitrary-cwd requirement concerns the application CLI and is not being extended to tests. Planned confirmation uses the pinned container with the project at `/candidate`, cwd `/candidate`, and the exact advertised root command; no host execution or model feedback. Historical Factory acceptance remains accepted regardless of the later independent semantic assessment.
