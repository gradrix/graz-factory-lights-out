# Independent QA: failed Stage 3 API run

## Outcome and identity

Frozen run `70a187241924`, runtime `25f75c3`, remains **interrupted after 900.03 seconds on attempt 2, not accepted**. No candidate, oracle, budget, or maintained source was changed. This is diagnosis and a disposable recovery experiment, not retrospective acceptance. SHA-256 identities and exact sandbox commands are in `qa-model-api-failed/receipt.json`; reproducible runner and probe are beside it.

## Findings

1. **Real documentation defect:** README instructs `uvicorn reservation_preview:app`, but the application object is `reservation_preview.app:app`; the package initializer is empty. A user following the published launch command cannot start the service. Correct the import target and give concrete offline wheel installation steps.
2. **Oracle overconstraint:** the final protected assertion requires the literal substring `pip` in README. The public task requires at least 40 words documenting new usage and errors, not that particular token or installer spelling. The README meets the word/endpoint checks and documents strict validation, stateless previews, accepted/shortage responses. Rejecting it solely for missing `pip` is unsupported by the stated contract. This does not excuse the separate broken launch command, which the checker misses because it starts the correct target itself.
3. **First-attempt generated-test defect, repaired:** the test assumed JSON output contains a space after `accepted:`. Compact JSON is valid. Attempt 2 permits optional whitespace and all 13 tests pass. Earlier test work also incorrectly assumed `bool` is not an `int` subclass.

## Implementation and test assessment

The endpoint aggregates repeated SKUs, rejects unknown SKUs, returns all original stock unchanged on any shortage, sorts deficient SKUs, and subtracts requests on successful previews. Pydantic models forbid extras, reject boolean/string integer coercion, enforce quantities 1–1000, stock 0–1,000,000, nonempty SKU strings, and at most 100 items. Empty requests, required fields, health, strict sum and missing-route behavior are covered. Domain logic uses new dictionaries and has no persistent reservation state. No material endpoint defect was found by source review and the exercised protected cases.

The 13 tests cover health/sum/404, aggregation, empty input, maximum item count, shortages, unknown SKU, extras, strict integer values, invalid ranges/shapes, missing fields and actual boolean output. They are meaningful, although the test named exact-fit uses a larger available stock; another aggregation case reaches zero. Build and egg-info artifacts remain from experimentation; they are cleanup residue rather than evidence of a functional failure.

## Repair-loop efficiency

Attempt 1 contains 24 requests, 24 responses and 25 tool events. Attempt 2 contains 10 requests, 9 responses and 12 tool events; the final request was pending at interruption. The feature implementation arrived early, but much of the budget was spent correcting verification mechanics:

- Invalid `pip wheel -o` and `-d` flags, then wheel-name/build corrections.
- Zero-test discovery and missing package marker, followed by missing imports from temporary installs.
- Repeated assumptions that `/tmp` persists between tools despite the stated ephemeral execution boundary.
- Test-client method/inheritance errors, HTTPX constructor misuse, synchronous use of asynchronous ASGI transport, and missing `base_url`.
- Incorrect boolean and JSON-whitespace assertions, plus an invalid ad hoc Python probe.
- `tail`/`grep` pipelines sometimes reported exit zero despite upstream failures, reducing the usefulness of exit-code feedback.

Attempt 2 turn 6 successfully built, installed and ran all 13 tests in one tool call. Turn 9's check then passed behavioral and generated-test checks but failed the README token assertion. The next model response did not arrive before the unchanged wall deadline. There is no final reviewer approval or accepted snapshot.

## Recovery route

Create a separately identified continuation from this frozen candidate. Repair README's launch target and add reproducible offline build/install commands; no endpoint change is indicated by this audit. Build, install and test within one ephemeral tool invocation, using direct subprocess return codes instead of masking pipelines. Run the unchanged original acceptance gate, installed-wheel tests, and a documented-command launch check. A new run must earn its own acceptance; preserve this failed result and original budget.

For a future fixture version, replace the undocumented `pip` token rule with a documented installation requirement or a behavior-based documentation check. Version that change explicitly and keep the original evaluation score frozen. Do not infer a Stage 3 overall result from this diagnosis.

## Verification boundary

Own verification uses the pinned Python 3.12 image `fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`, explicit runc, no network, non-root user, read-only input mounts, one CPU, 512 MiB memory and bounded time. Dependencies come only from the existing approved offline wheelhouse. No inference calls or GPU runtime were used. The diagnostic oracle copy removes only the literal `pip` predicate; a separate disposable README repair is checked against the untouched original oracle. Results are recorded in the sibling receipt.

Observed supplemental results: original oracle **fails only documentation token**; diagnostic predicate removal **passes**; documented import **fails**; correct import **passes**; README-only disposable repair **passes the untouched original oracle**. Each passing full oracle run includes offline wheel installation, live loopback HTTP cases, and 13 discovered tests. Initial probe setup omitted explicit tmpfs exec and could not load native dependencies; corrected sandbox execution is the final reproducible receipt and is not counted as a candidate failure.

### Follow-up: generated build residue

Read-only inspection of the rig's actual `change.patch` at `/home/gradrix/gflo-stage3-25f75c3/.gflo/stage3-model/70a187241924` confirms that it includes `build/lib/reservation_preview/*` and five `src/gflo_reservation_preview.egg-info/*` files: patch SHA-256 `cc91738073669ebbf58f55084b0ce5f8bf4c4f376683b506948d3f04f874a263`, 15 files, 260 insertions, 6 deletions. This is the recorded failed-attempt patch, not an accepted or necessarily final-attempt snapshot. The captured final workspace has nine generated files totaling 2,364 bytes; all four build Python files are byte-identical to their source counterparts.

This is bounded candidate hygiene residue, with no demonstrated functional or acceptance-integrity defect. Factory's force-add faithfully includes it, and `review.load_files` exposes these text files to the reviewer. The run never reached accepted review. Recommend removing these generated directories in a separately identified repair and building from a disposable copy. Treat residue as a minor reviewer finding here; there is no evidence justifying a core acceptance filter or blanket build-directory ban. Preserve force-add's complete snapshot behavior rather than silently hiding submitted files.
