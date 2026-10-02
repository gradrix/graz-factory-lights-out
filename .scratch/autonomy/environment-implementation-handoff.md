# Stage 3 implementation handoff

Prepared 2026-10-02 while Stage 2 cohort C is running. Planning only; Stage 2 acceptance remains the gate for maintained changes. Follow [ADR 004](../../docs/decisions/architecture/004-environment-snapshots.md) and the [security review](../../docs/research/environment-security-boundary.md). The private helper is evidence, not implementation to copy.

## Smallest complete slice

Implement one guarded preparation lifecycle and one immutable receipt/artifact store, with three explicit recipes: Python stdlib, packaged Python API and CommonJS Node/TypeScript. Prepare environments explicitly before task creation; running/resuming a task stays offline. Models may request a new supported environment but cannot mutate a run's frozen environment or provide Docker arguments, host paths or arbitrary dependencies.

Use one cohesive `gflo/environment.py` initially for recipe validation, preparation, strict artifact validation, publication and resolution. Split only if the security-sensitive archive implementation obscures its contract. Keep Docker execution in Sandbox/guardian. No general build framework, dependency solver or package registry service.

### Existing seams and proposed changes

| Existing seam | Small change |
| --- | --- |
| `gflo/__main__.py` currently reads JSON configuration then creates one `Sandbox(config.image)` and model worker | Add `environment prepare`, `environment inspect` and `environment check` branches before model-worker construction. Preparation never needs model credentials. Keep config parsing here; there is no `gflo/config.py`. |
| `Factory._create` snapshots task/acceptance and hashes frozen `task.json` | Resolve an environment receipt before writing the frozen task. Store receipt ID and receipt hash in task, copy immutable runtime facts into run evidence, and bind them through existing contract hashing. |
| `Factory._resume` validates task/acceptance then invokes worker/verifier | Resolve and verify the same environment before any command. Missing/tampered artifacts fail closed. Do not substitute the current configured image. |
| `Sandbox.execute` owns fixed Docker arguments; `verify` already receives task | Accept a validated environment object, never raw receipt paths/mount arrays. Python/Node mounts and environment variables come from fixed profile policy. Worker `run` calls must receive the same frozen object as acceptance checks. |
| `ModelWorker.__call__` currently assumes stdlib in SYSTEM and calls `execute` without task | Supply actual profile/runtime facts and environment identity. Update the assumption and pass the validated binding for every `run` and `check`. |
| `Reviewer.__call__` currently sends only objective and files | Add compact trusted runtime facts to review input. Preserve direct `review_files(objective, files)` callers through an optional context parameter. |
| `gflo.guard` supervises create/start and owner-pipe EOF | Extend one bounded executor protocol to preparation and artifact streaming; preserve strict controller-generated arguments. Do not leave producer/receiver outside cancellation supervision. |

Prefer an optional `environment` argument on Sandbox execution rather than a mutable global “current environment.” This prevents separate tasks from accidentally inheriting another task's receipt and keeps direct tests straightforward. The resolver owns the artifact root; receipt ID is a validated identifier, never a filesystem path supplied by a model.

## Immutable binding and compatibility

New tasks may name a prepared receipt ID. If omitted, freeze a synthetic stdlib receipt for the **inspected actual image ID** selected by legacy `config.image`/DEFAULT_IMAGE. Capture actual Python version; do not infer it from a tag. Config changes after creation cannot change the runtime of the frozen task. Environment identity covers recipe revision, platform, base image, lock hashes and canonical dependency-tree hash.

Old runs without an environment field have no historically frozen image evidence. Preserve their existing resume behavior as explicitly `legacy_unbound`; never rewrite their frozen task/hash or claim retroactive binding. New acceptance must not promote legacy receipts into Stage 3 evidence. Existing CLI/config continue to work; new prep/check commands do not contact inference. Existing accepted runs remain readable.

Snapshot publication is same-filesystem staging → atomic rename of a complete controller-owned directory after smoke evidence. Receipt/tree tampering invalidates use. Canonical tree identity covers sorted relative paths, regular-file bytes and selected execution modes; reject links. Mount read-only, keep artifact roots outside writable task paths, and permit no untrusted writers between validation and run. Cancellation revokes publish eligibility before cleanup and is rechecked immediately before publication.

## Publish only reusable recipe inputs

Promote a small reviewed subset from `.gflo/environment-locks` into a proposed `environments/` directory:

- Python complete `requirements.lock`; normalized package name/version/URL/SHA-256 list derived from `resolution.json`; the API fixture's exact build-backend requirement `setuptools==78.1.0`.
- Node `package.json` and `package-lock.json` with TypeScript 5.8.3, @types/node 22.15.3 and undici-types 6.21.0. Retain npm flags affecting resolution. Omit `.bin` links by precise policy and call the compiler's real path.
- A short versioned recipe JSON for each profile: platform, immutable base ID and repository identity, expected runtime family, fixed commands, package artifact list, scratch/resources and smoke checks.
- Independent scenario sources/checkers from `.gflo/environment-qualification`, copied into maintained fixtures with source hashes and split into writable project and protected acceptance inputs. Do not modify the frozen originals.

Do **not** publish extracted dependency trees, npm cache, wheel binaries, private container receipts, full pip metadata or probe scripts as source recipes. Keep acquired bytes and prepared snapshots in a gitignored environment store. Do not transplant `.gflo/environment-locks/prepare.py`: security review reproduced duplicate-path overwrite and destination-symlink escape in its extraction helper.

The tested local bases were Python image ID `sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc`, repo identity `python@sha256:3d5ed973e45820f5ba5e46bd065bd88b3a504ff0724d85980dcd05eab361fcf4`, Python 3.12.13/pip 25.0.1; and Node image ID `sha256:88f8ba583a884279252779bbe221bf1ff2c61cf236cc973f8ca97676ae6d07f0`, repo identity `node@sha256:43ac6c60b8f89723f746e8a92ce91abd5017e627ce1ddfe4238355d3a30b772c`, Node 22.23.3/npm 10.9.9. Both are linux/amd64. Validate selected platform/image mapping and actual runtime on the target; the rig's older Python base is different.

## Lifecycle and safety gate

1. Validate fixed recipe and complete locks before acquiring any bytes. Initial support matches approved package sets; manifest inference proposes one of these profiles. Unsupported changes return an actionable environment request instead of silently resolving a new graph.
2. Network fetch gets sanitized dependency inputs only. Verify every URL and artifact hash; no repository `.npmrc`, pip config, model configuration, source checkout or credentials. Assembly/project-wheel execution uses `network=none` and never falls back online.
3. Actual preparation executors use explicit approved `runc`, non-root UID, read-only root, dropped capabilities, no-new-privileges, no GPU request, memory=swap≤1 GiB, CPU≤1 and PID≤128. Cap **all** writable mounts, including shared memory; e.g. `/work` 480 MiB, `/tmp` 16 MiB, `/dev/shm` 16 MiB. Store inspect plus device/mount/environment evidence. Private local probes used `Runtime=nvidia`; do not claim their null DeviceRequests established GPU exclusion.
4. Bound logs, stream bytes, total elapsed time, archive entries/expanded bytes and host staging. Validate the complete archive before extraction into a fresh private directory. Reject duplicate normalized paths, path-prefix conflicts, sparse/PAX encodings outside the explicitly supported subset, traversal, hard/symbolic links and special files. Create files without following links or overwriting; normalize modes/owners. Skip only the defined npm link layout.
5. Supervise owner death, explicit cancellation and stream deadlines through actual executor removal. No late publication; cleanup failure blocks reuse. Preserve the previous good receipt after any failure.
6. Offline smoke checks produce receipts. Bind Python `/opt/deps` and Node `/node_modules` via fixed profile policy. Python project-wheel builds use locked backend, `--no-build-isolation --no-deps`; source/wheel identity stays separate from reusable dependencies. Avoid worker-side package downloads.

## Acceptance contract and commands

These are proposed interfaces/tests to implement, **not commands available today**. Use a private disposable store; do not prune shared images or caches.

```sh
python3 -m unittest discover -s tests -p 'test_environment*.py'
python3 -m unittest discover -s tests -p 'test_sandbox.py'
python3 -m unittest discover -s tests -p 'test_worker.py'
python3 -m unittest discover -s tests -p 'test_runner.py'
python3 -m unittest discover -s tests -p 'test_cli.py'
python3 -m unittest discover -s tests -p 'test_review.py'
python3 -m gflo environment prepare python-stdlib-v1 --store .gflo/qualification-envs/stdlib --receipt-out .gflo/stdlib-receipt.json
python3 -m gflo environment prepare python-api-v1 --store .gflo/qualification-envs/api --receipt-out .gflo/api-receipt.json
python3 -m gflo environment prepare node-ts-v1 --store .gflo/qualification-envs/node --receipt-out .gflo/node-receipt.json
python3 -m gflo environment check RECEIPT_ID_FROM_PREPARE --store .gflo/qualification-envs/api --repeat 2
```

Replace `RECEIPT_ID_FROM_PREPARE` with the returned receipt ID. Repeat checks for stdlib and Node using their stores. Task and CLI operands are receipt IDs; `--receipt-out` writes evidence only and never authorizes embedded mount paths.

The implemented test gate must cover malicious archives; forbidden dependency URLs; lock/manifest mismatch; missing/corrupted offline artifacts; receipt/tree tampering; config image change after task creation; reuse/resume with immutable binding; cancellation during fetch, archive receive, smoke and publication; owner SIGKILL; daemon cleanup failure; disk/memory/PID limits; no credentials/socket/GPU devices; and unchanged prior-good receipt. Tests should prove behavior, not duplicate helper internals.

Profile scenarios: stdlib CLI valid/empty/malformed/type-invalid input and exit codes; API offline built/installed wheel, real loopback HTTP success/422/404; Node strict TS compile, Node type resolution, runtime valid/invalid/overflow inputs. Each starts with empty package cache and no snapshot, explicitly recording reused base images, then passes twice in fresh offline containers with no pulls. Keep checks outside the coder mount.

Finally use the frozen environment on one bounded local-model task per profile, with independent checks and review. Reviewer context includes image/snapshot identity, Python 3.12 facts (including f-string grammar), Node/npm/tsc versions and exact checks. A wrong-version objection requires target-runtime evidence. Runtime preparation passing does not establish model-task success.

## Remaining choices and defaults

- **Public-only egress:** bridge networking plus registry settings is not an enforced boundary. Default to fixed approved URL manifests and a bounded trusted downloader that validates redirect destinations and resolved addresses, rejects private/loopback/link-local targets, and connects to the validated address while preserving TLS hostname verification. Qualify DNS/redirect cases. If implementation instead uses broader bridge egress, explicitly mark it unresolved and avoid a public-only claim; obtain security acceptance before promotion.
- **Base acquisition:** explicit prep may fetch the exact approved repository digest; run/resume never pulls. Cold package-cache qualification may reuse a recorded base. Do not claim a completely cold host when base images were reused.
- **Dynamic dependencies:** defer automatic arbitrary version resolution. New dependencies require a reviewed recipe/lock revision; initial manifest inference only selects known supported recipes. This is the smallest supported interpretation of three fixed profiles.
- **Security gate:** independent security verification of the implemented candidate is required. The private feasibility helper's successful profile checks do not waive archive, device or cancellation requirements.
