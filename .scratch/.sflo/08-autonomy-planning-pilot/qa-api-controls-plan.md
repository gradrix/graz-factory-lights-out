# Supplemental API paired controls — prepared, not executed

No candidate imports, builds, containers, model calls or rig calls occurred during preparation. Wait for root's explicit post-arm execution instruction. These controls validate supplemental assertions; they neither repair retained candidates nor change frozen acceptance.

## Source and reproducibility

`qa-api-control-fixtures.py` verifies the complete frozen private `config-preview` reference against its original reference manifest, copies it into a new private output directory, then creates three separately labelled disposable mutants. It never imports or executes any project code. An existing output directory is refused. All resulting files, original reference identity, probe script identity and expected probe outcomes are recorded in the generated manifest.

After root authorizes execution, prepare with:

```sh
python3 qa-api-control-fixtures.py --reference PATH_TO_FROZEN_PRIVATE_REFERENCE/config-preview --reference-manifest PATH_TO_FROZEN_PRIVATE/reference-manifest.json --output NEW_PRIVATE_CONTROLS_DIRECTORY
```

Run `qa-api-probes.py --project /workspace` once for each of the four control directories in the exact approved API environment. Use explicit `--runtime runc --network none --pull never`, immutable approved image ID, read-only rootfs and `/workspace`, read-only prepared dependencies at `/opt/deps`, and a bounded writable `/tmp` (192MiB), memory1GiB and pids128. The script asserts CPython3.12.13 and builds/installs only a copied project offline. Capture complete stdout/stderr and Docker invocation/exit facts outside the mount. A controller timeout must clean the exact owned container. Root supplies approved paths/image/dependency identity; no fresh dependency fetching or image fallback.

## Paired expectations

| Control | Expected result |
| --- | --- |
| Frozen conforming reference | Every supplemental probe passes; original reference bytes unchanged. |
| Scalar-depth mutant | Depth7 scalar and post-insertion depth7 probes fail, for API and HTTP; depth6 controls still pass. |
| Missing FastAPI Body binding mutant | Valid HTTP preview requests fail while corresponding direct Python probes still pass. |
| Validate-operations-lazily mutant | Earlier conflict incorrectly precedes a later invalid value/shape; API and HTTP shape-priority probes fail. Ordinary nested test still passes. |

Compare named probe outcomes against each generated manifest entry. Required rejection is a passing assertion. A nonzero process exit alone does not demonstrate detection: each mutant must fail the intended named probes, and its named unaffected controls must still pass. The reference must pass the exact same assertions. Unexpected reference failure makes the affected probe provisional pending diagnosis; preserve all original outputs and version any correction.

## Own-probe audit

B1 validates each operation value independently at root depth0. The post-insertion probe intentionally uses the otherwise valid value `{'x':0}` at path length6 beneath an existing depth5 parent. Its inserted object is depth6 and scalar is depth7: this is B3 `Conflict(index=0,code='limit')` / HTTP409, not malformed-value422. `chain(6)` ends in a scalar at depth6 and is valid; `chain(7)` ends at depth7 and must reject even though its deepest object is only depth6.

The HTTP priority probes use a well-shaped initial remove of a missing key followed by an operation value invalid **in isolation** (depth7 or201nodes). Complete original request validation must therefore raise ordinary ValueError / HTTP422 before the earlier would-be missing conflict. The lazy-validation mutant demonstrates that distinction. Separately, a200node value is valid alone but adds the document root on insertion, producing201nodes and Conflict409.

The probes use deep-copy snapshots and strict recursive type/value equality. They distinguish boolean versus integer recursively, null presence versus absence, and verify before/after audit snapshots independently from input aliasing. README command lines are evidence for semantic review, not mandatory lexical tokens. The script runs the exact requested installed-package unittest command from an unrelated working directory and retains its output; meaningful test coverage and the stated README commands remain separate semantic-review obligations.
