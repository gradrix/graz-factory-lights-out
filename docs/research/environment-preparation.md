# Stage 3: trusted environment preparation

Checked: 2026-10-02. Design research only; no image was pulled, built or executed. Stage 3 remains unimplemented and unaccepted. The [roadmap](../roadmap.md#3-automatic-environment-preparation) requires three cold preparations followed by two offline checks per profile, plus bounded failure and cancellation evidence.

## Small implementation boundary

Add one preparer with three versioned templates and a serial lifecycle: validate → fetch → assemble → smoke-test → publish receipt. Its input contains `profile`, `template_revision`, `platform`, manifest/lock content hashes and budgets. The controller chooses an approved template; model output can propose dependencies but cannot supply Dockerfile instructions, shell fragments, arbitrary registry URLs, mounts or build flags. Infer a proposal from `pyproject.toml`, locked requirements, `package.json` and `package-lock.json`; conflicting or unsupported manifests yield a concrete environment request.

The output is an immutable environment receipt, image identity and smoke evidence. Keep the previous successful receipt/image while preparing a replacement; publish only after checks pass. Environment changes enter stage 2 review before adoption. A lookup by input hash is sufficient initially; no plugin framework or general dependency solver is needed.

Current [Sandbox](../../gflo/sandbox.py) already uses `--pull never`, `--network none`, a read-only root, non-root UID, dropped capabilities, no-new-privileges, CPU/memory/PID limits and bounded temporary storage. [Its guardian](../../gflo/guard.py) removes the named container on timeout or owner-pipe EOF. On this host, read-only inspection found default image `sha256:a8a3e0a84b0d5fab2b3b4b32e89715a7384b7af2f81b5e82d203d12828cb2578`, platform `linux/amd64`, with no repository tags or repository digests. This is a local image ID; registry provenance and its runtime versions were not established by that inspection.

## Exact starting profiles

| Profile | Proposed boundary | Independent smoke scenario |
| --- | --- | --- |
| `python-stdlib-v1` | CPython 3.12, standard library only; select and record an exact patch/base digest before qualification | JSON CLI with valid and invalid input, exit codes and `unittest` |
| `python-api-v1` | Same Python; FastAPI, basic Uvicorn and HTTPX; wheel-only dependencies; no native source builds | Packaged API with valid request, validation failure and loopback HTTP response |
| `node-ts-v1` | Node 22; select exact supported patch and bundled npm version; TypeScript and Node types; no native addons/install scripts | Compile a TypeScript JSON CLI to `/tmp`, execute it and run Node's test runner |

Python 3.12 is an explicit target choice, not a claim about the host interpreter. Node lists support phases by major release; verify the selected Node 22 patch remains appropriate at qualification time. [Python 3.12 documentation](https://docs.python.org/3.12/), [Node release schedule](https://nodejs.org/en/about/previous-releases).

Concrete initial dependency candidates were verified to exist through official registry APIs on the checked date. They are bounded scenario fixtures, not latest-version or security recommendations. Resolve and retain their complete transitive closure for the chosen platform before accepting any lock:

| Candidate | Registry evidence |
| --- | --- |
| FastAPI `0.115.12` | [PyPI metadata](https://pypi.org/pypi/fastapi/0.115.12/json), Python ≥3.8 |
| Uvicorn `0.34.2` | [PyPI metadata](https://pypi.org/pypi/uvicorn/0.34.2/json), Python ≥3.9 |
| HTTPX `0.28.1` | [PyPI metadata](https://pypi.org/pypi/httpx/0.28.1/json), Python ≥3.8 |
| TypeScript `5.8.3` | [npm metadata](https://registry.npmjs.org/typescript/5.8.3), Node ≥14.17 |
| `@types/node` `22.15.3` | [npm metadata](https://registry.npmjs.org/@types/node/22.15.3); lock its transitive dependencies too |

For example, PyPI reported SHA-256 `e94613d6c05e27be7ffebdd6ea5f388112e5e430c8f7d6494a9d1d88d43e814d` for `fastapi-0.115.12-py3-none-any.whl`. npm reported TypeScript integrity `sha512-p1diW6TqL9L07nNxvRMM7hMMw4c5XOo/1ibL4aAIGmSAt9slTE1Xgw5KWuof2uTOvCg9BY7ZRi+GaF+7sfgPeQ==`. These examples are not complete locks or proof the packages work together.

## Fetch once, execute offline

1. **Validate and freeze.** Require an exact template, platform and approved registry; reject VCS, arbitrary URL/path dependencies and unsupported install hooks. Missing locks produce a separately reviewable lock proposal in a disposable preparation directory. Freeze full Python versions/hashes or npm lockfile integrity and all resolution flags. Hash the source manifests too.
2. **Fetch with network.** Use a dedicated bounded preparation container with an empty task cache. Give it only sanitized dependency manifests and a writable artifact directory. Python uses `pip download --require-hashes --only-binary=:all: -r requirements.lock -d /artifacts/wheels` in the target runtime. npm uses `npm ci --ignore-scripts --no-audit --no-fund --cache /artifacts/npm-cache` with the pinned npm version; retain the lock and cache, then test cache completeness offline. Avoid copying repository `.npmrc`, home directories or host pip configuration.
3. **Assemble from trusted input.** Pin the base as `repository@sha256:...`, record the selected platform manifest and local image ID. Use the template and fetched artifacts as the entire build context. Python installs to `/opt/venv` with `--no-index --find-links=/wheels --require-hashes --only-binary=:all:`. npm installs from the retained cache with `npm ci --offline --ignore-scripts --no-audit --no-fund`. A missing artifact fails; no online retry occurs in this phase.
4. **Run with existing Sandbox restrictions.** Dependencies live outside `/workspace`, whose bind mount would hide image content installed there. Use `/opt/venv/bin/python` for Python. For Node, copy the frozen workspace to bounded `/tmp/project`, attach a read-only `/opt/deps/node_modules` symlink there, compile into `/tmp`, and execute tests from that copy. This preserves ordinary module resolution and a read-only acceptance source. Lock/manifest changes invalidate the receipt before execution.

pip requires every dependency to be pinned and hashed in hash-checking mode, and documents wheel-only installation to avoid source distribution execution. Its wheelhouse supports offline installation. [Secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/), [repeatable installs](https://pip.pypa.io/en/stable/topics/repeatable-installs/).

npm says `ci` exits on manifest/lock mismatch and does not rewrite locks. Preserve the install flags used to create the lock. `ignore-scripts` disables install lifecycle scripts; explicitly invoked project scripts still execute. npm defines offline mode as “no network requests will be done during install”; `prefer-offline` can fetch missing data. [npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci/), [offline configuration](https://docs.npmjs.com/cli/v11/using-npm/config/#offline), [lockfile format](https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json/).

For the packaged Python fixture, start with a fixed supported build backend whose wheel and dependencies are also locked. Build/install the project's wheel offline in writable scratch using that backend and `--no-build-isolation --no-deps`; do not execute project build code in the network-enabled fetch phase. Record the project source/wheel digest separately from the reusable dependency image. Python environments are not generally portable; create `/opt/venv` at its final path inside the final runtime image. [Python venv portability](https://docs.python.org/3.12/library/venv.html#how-venvs-work).

Docker notes that tags are mutable and digest pinning fixes the selected base. `RUN --network=none` or build `--network=none` controls build instructions; it does not prohibit builder-side base/frontend resolution. Provision those inputs explicitly in the fetch phase; prove offline assembly separately if claiming it. The initial acceptance claim is offline worker execution twice, not bit-identical rebuilding. [Base pinning](https://docs.docker.com/build/building/best-practices/#pin-base-image-versions), [build options](https://docs.docker.com/reference/cli/docker/buildx/build/), [Dockerfile network modes](https://docs.docker.com/reference/dockerfile/#run---network).

## Receipt and reviewer context

Persist template revision/hash; normalized request; source manifests and complete locks; registry URLs; fetched artifact hashes; base index/platform digest; resulting local image ID and OCI/registry manifest digest when available; actual interpreter/package-manager versions; platform; commands; exit codes; bounded logs; durations; cancellation/cleanup result; and smoke evidence. Do not describe an image ID as a registry manifest digest. Retain an OCI archive or equivalent image export plus its checksum for a locally built image without a registry. Exact identity and repeatable dependency selection do not establish bit-identical builds.

Give the local reviewer the receipt before the diff: target `sys.version`, `sys.executable`, `sys.platform`, dependency versions, Node/npm/tsc versions where applicable, image identity and exact check commands/results. State explicitly that Python syntax/API claims are evaluated against the recorded target, including Python 3.12's f-string grammar, rather than the review host's version. A version-sensitive finding must cite the target requirement or reproduce in that same image; otherwise record it as unverified. This prevents unsupported compatibility assumptions from becoming blocking defects. [Python 3.12 syntax changes](https://docs.python.org/3.12/whatsnew/3.12.html#pep-701-syntactic-formalization-of-f-strings).

## Boundaries and acceptance evidence

The trusted host controller alone accesses Docker. Fetch/build/worker containers receive no Docker socket, host credentials, SSH agent, cloud credentials or model-serving secrets. The first profiles use public dependencies and need no build secrets. If private registries are later supported, scope secrets to preparation using secret mounts; Docker warns against persisting secrets through build arguments or environment variables. [Docker daemon security](https://docs.docker.com/engine/security/), [build secrets](https://docs.docker.com/build/building/secrets/).

Proposed initial budgets: 10-minute total preparation deadline, 60-second individual fetch timeout with at most one retry, 2 CPUs, 2 GiB RAM, 256 PIDs, 2 GiB artifact quota and bounded log tails. Keep the current worker budget unless a fixture demonstrates a need to change it. Enforce disk quota with a dedicated quota-backed directory/volume; a time limit alone does not bound disk use. Apply resource limits to the actual preparation/build executor; limiting the Docker CLI process does not limit daemon-side builds. A dedicated resource-bounded builder must be inspected and tested before use. [Docker resource limits](https://docs.docker.com/engine/containers/resource_constraints/).

Qualification must retain evidence for each case:

- Each profile starts with empty task package caches and no profile image. Record any intentionally shared base/builder inputs; a fully cold claim requires those absent too in a disposable builder store, without pruning shared host images.
- Two fresh offline worker containers run the complete scenario against the same receipt, `--pull never` and `--network none`; confirm successful loopback tests and failed external connectivity. No dependency installer needs registry access.
- A nonexistent package, denied/unavailable registry, lock mismatch, corrupted wheel/npm artifact and absent offline artifact each fail within budget with package/phase/reason and a useful next action.
- Memory, process and disk exhaustion stay confined; retain exit/OOM evidence and distinguish resource failure from incorrect product behavior.
- Cancel during fetch, assembly and smoke, and kill the owner abruptly. Require confirmed executor removal, no late publish and no surviving writer before retry. Docker/build daemon outage becomes cleanup failure, not successful cancellation. Reuse the guardian pattern but do not assume it already controls build jobs.
- Inspect actual mounts and environment for credential/socket absence. Reject lock changes without a new environment revision. A failed revision leaves the known-good receipt usable.

No scenario above was executed in this research pass. The next implementation should deliver these three profiles and receipts with their failure tests before adding another language or a general build system.
