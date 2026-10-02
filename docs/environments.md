# Local execution environments

GFLO prepares a pinned base image plus a read-only dependency snapshot. A task records the snapshot receipt before inference. Commands, acceptance checks and resumed runs validate that same receipt, even if the configured default image changes. Accepted status is invalidated if its environment changes. Historical tasks without a receipt remain `legacy-unbound`.

## Supported recipes

| Profile | Runtime and approved dependencies | Project inputs |
| --- | --- | --- |
| `python-stdlib` | CPython 3.12.13 standard library | No package declarations |
| `python-api` | CPython 3.12.13; FastAPI 0.115.12, Uvicorn 0.34.2, HTTPX 0.28.1, Pydantic 2.13.5, setuptools 78.1.0; complete transitive lock | `pyproject.toml` with the approved runtime/build dependencies and Python range |
| `node-ts` | Node 22.23.3, npm 10.9.9, TypeScript 5.8.3, Node types 22.15.3, undici types 6.21.0 | CommonJS `package.json` and the approved complete `package-lock.json` |

The exact recipes and artifact hashes are under `gflo/recipes/`. These are deliberately constrained profiles. Unsupported dependency versions, custom build backends, Node workspaces/overrides/scripts and mixed projects without an explicit profile produce errors. They require a separately tested recipe change.

## Prepare once, execute offline

Provision the exact base image first; GFLO never pulls a base during preparation or execution. The approved Python and Node image IDs are defined in `gflo/sandbox.py` and `gflo/prepare.py`.

```sh
python3 -m gflo environment prepare python-api --project /path/to/project
python3 -m gflo environment inspect RECEIPT_ID
python3 -m gflo environment check RECEIPT_ID --repeat 2
python3 -m gflo run task.json --environment RECEIPT_ID
python3 -m gflo resume RUN_ID
```

Environment commands need no model configuration or credentials. Use `environment --store /path/to/private/store ...` and `run --environment-store /path/to/private/store ...` to select another store. The directory must belong to the controller and have mode 0700. Receipt IDs are hashes, never mount paths.

Without `--environment`, `run` uses the task's explicit `profile`, or selects a profile from its manifests, validates its declarations and prepares it. **That preparation can require registry access.** Pass an existing receipt ID for operation without internet access. Resuming a bound run never downloads dependencies. An interrupted or failed publication is unusable; an existing good receipt is preserved.

Python dependencies are mounted at `/opt/deps` through `PYTHONPATH`. API acceptance builds and installs the project wheel offline in fresh scratch space before running generated tests. Node dependencies are mounted at `/node_modules`; invoke `node /node_modules/typescript/bin/tsc` directly. Convenience `.bin` links are omitted. Project files persist between worker commands; installations in `/tmp` do not.

## Preparation boundary

A trusted client downloads only the fixed, hash-pinned artifacts from the approved HTTPS registries. It checks public IPv4 destinations and TLS hostnames, rejects redirects/proxies and bounds response bytes. This is a client policy, not a network firewall. No project or fetched package code runs in the online container. Offline assembly uses immutable approved inputs, empty disposable package caches and disabled package scripts.

Containers use runc, a nonroot user, a read-only root, no capabilities and no-new-privileges. Preparation limits are 1 GiB memory/swap, one CPU, 128 PIDs, 16 MiB shared memory, 480 MiB work scratch and 16 MiB temporary scratch. Binary output is capped at 128 MiB; extracted dependency trees are capped at 96 MiB and 16,384 paths. The default preparation deadline is 180 seconds plus bounded cleanup time. There are no host writable mounts, Docker socket, model credentials or GPU devices in the preparation recipe.

The guardian removes its exact container after cancellation or controller death. Archives are fully validated before extraction. Publication binds image, recipe, complete locks, artifact hashes, actual runtime, normalized dependency bytes/modes and offline check receipts. Transport closure and temporary-tree cleanup must succeed before publication commits. Persistent pending markers prevent reuse of incomplete publication.

## Qualification status

Stage 3 is still active. Candidate `25f75c3` passed three cold package-cache preparations and six offline smoke checks on MONSTER-GAMING-PC. Independent local QA also passed six realistic reference checks, including API wheel installation and actual HTTP requests, and strict TypeScript compilation. Shared base images were reused; these were not completely cold hosts.

Packaged regression execution and the outer cleanup/publication boundary passed repair rechecks. Independent lifecycle, input-failure and security checks passed. The original three-task local-model cohort accepted stdlib; API and TypeScript reached their 15-minute deadlines. Their executable code passed independent diagnosis, but documentation was incomplete or wrong and two oracle defects were identified. Original results remain failed. Fresh independently checked tasks are testing a faster 96K/Q4 serving profile before Stage 3 acceptance. The authoritative progress and exact evidence links are in [the execution record](../.scratch/.sflo/04-autonomy-environments/run.md).
