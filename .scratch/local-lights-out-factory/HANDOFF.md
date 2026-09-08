# GFLO handoff — await the RTX 5090 target

## Current state

Research and architecture planning are recorded in [the map](map.md). Decisions through [Prototype the reference architecture](issues/11-prototype-the-reference-architecture.md) are resolved as design choices, not hardware-tested feasibility claims. [Plan the staged implementation and validation](issues/12-plan-the-staged-implementation-and-validation.md) contains the proposed stage sequence and remains claimed pending final agreement.

The HTML lifecycle demo is a throwaway in-memory simulation, not a running factory. JavaScript syntax and Git whitespace checks have passed. Browser behavior, real inference, isolation, durable recovery, and coding capability have not been validated here. No production factory implementation or model runtime has been installed as part of this checkpoint.

## Latest user constraint

The user is away from the RTX 5090 until later and considered temporary inference on this Acer or an M3 Pro MacBook. Recommended course: preserve this checkpoint and wait for the intended GPU target for the first model-capability experiment. A temporary backend may later help with transport/plumbing tests, but its results must not qualify the intended RTX 5090 model/runtime profile. Do not install a temporary model merely to keep activity going.

## Accepted deployment decision

- Keep the small Python bootstrap/serving launcher on the host. Containerizing it solely to give it a Docker socket is not required.
- Build the initial controller as ordinary testable Python, then package it into its own versioned container with persistent ledger/artifact storage before unattended operational validation. This controller is not implemented yet.
- Run managed inference in a separate GPU container, or connect to an independently operated endpoint. Local inference is first-class; remote/cloud-compatible endpoints require explicit configuration and no automatic fallback exists.
- Run generated product code in disposable isolated development containers from the first live pilot. Execute acceptance tests in separate clean environments, with trusted evidence collection outside candidate control.
- Keep container-management authority in a narrow trusted broker; coding workers must not receive its Docker socket, credentials, writable ledger, or active controller files. A container with broad Docker access is not a sufficient isolation guarantee.
- Factory self-development operates on a candidate Generation in isolated environments. The separate launcher may eventually promote a validated candidate or roll back; workers do not modify the active controller in place. Automatic self-upgrade is not implemented.

## Current implemented slice

The [serving launcher](../../scripts/serve.py) and [usage documentation](../../infra/serving/README.md) provide `config`, `doctor`, `up`, `status`, `smoke-test`, and `down`, using Python 3.10+ standard library only. This is explicitly authorized infrastructure preparation, not completion of the wider factory stages.

External mode defaults to loopback and never manages Docker. Non-loopback endpoints require explicit opt-in and HTTPS; private HTTP GPU endpoints can be reached through an independently configured SSH tunnel. Credentials are referenced by environment-variable name, not stored in tracked configuration. Redirects and ambient HTTP proxies are disabled. Readiness checks send no generation prompt; the explicit smoke test sends only fixed synthetic content. Full cloud-provider compatibility and product-data egress policy are not implemented.

Managed mode supports SGLang only, with a pinned image digest and checkpoint revision, one GPU and one inference request at a time. It reuses a matching running container, restarts a matching stopped container, refuses running configuration drift, and checks ownership before lifecycle changes. Model-cache volumes survive stops/replacement. A per-user/service lock serializes launcher mutations. It rejects remote Docker daemons, does not install host drivers, and is not the worker sandbox.

The managed example intentionally requires selecting a verified image digest; its researched Qwen checkpoint and settings are not a validated GPU recipe. No runtime image or model weights have been pulled or launched here. Host preflight is partial: actual container GPU access, disk reserves, enforced memory/PID limits, restart behavior, credential rotation, model fit, and numerical quality still need target validation or further implementation.

## Verification and limitations

Run `python3 -W error::ResourceWarning -m unittest discover -s tests -v` from the repository root. The suite uses mocked Docker and a loopback-only HTTP server to exercise configuration validation, lifecycle reuse/drift/ownership, deadlines, external-mode separation, authentication handling, redirect refusal, and synthetic response validation. Also run `python3 scripts/serve.py config`, Python/HTML-script syntax checks, and `git diff --check`.

These checks do not qualify actual Docker/SGLang startup, GPU loading, downloads/cache reuse, container security, large-context operation, or coding quality. No browser behavior test of the throwaway HTML prototype has been performed. The checkpoint is suitable for continuing development and target verification, not a claim that every integration path was tested.

Checkpoint result: 25 launcher tests passed with resource warnings treated as errors; external configuration validation, Python compilation, prototype JavaScript syntax, and Git whitespace checks passed. No real GPU service was started to obtain these results.

## Remaining work and resume path

1. Pull the latest checkpoint from `origin/main` on the destination checkout after the requested push is verified. Git transports repository artifacts, not local conversation/session state or credentials. The preceding planning checkpoint was `0f6704a`; the new launcher/handoff checkpoint follows it.
2. Read this handoff, the map, and the staged-plan ticket. Preserve the accepted defaults: small worker views; tests-first dynamic diagnosis/repair; scheduler-owned work and evidence; on-demand planning; no SFLO/Gas City runtime dependency; profile-driven output languages.
3. Confirm the proposed first implementation scope: Stage 0 target verification and Stage 1 durable worker loop plus the twelve-task live pilot. Do not implement later layers before pilot evidence.
4. Locate the actual GPU host and endpoint; inspect driver/runtime/checkpoint/tokenizer, memory, cache storage and enforced execution controls. Choose external mode for an existing service, or set the verified managed image/checkpoint pins. Run preflight, startup, readiness and synthetic inference there. Test repeated startup, stopped restart, drift refusal and preserved cache on the actual backend. Do not assume the destination is already provisioned or the researched checkpoint is available.
5. Create bounded implementation tasks for the durable controller/ledger, artifacts, execution broker, worker views, model client and gate runner. Validate mechanics with deterministic doubles, then run the twelve-task real-model pilot. Retain failed results and revise context/tool/task policies before expanding.
6. Add dynamic diagnosis/repair and dependency-aware integration only as the staged evidence supports them. Containerize the controller before unattended validation, then progress through maintenance, another language, mixed-stack changes, scale, operational recovery and eventual candidate self-upgrades. No manager hierarchy or general multi-backend platform is needed for the first pilot.

The user requested committing and pushing this repository checkpoint. That does not authorize production deployment, host migration, or publication of generated products. The benchmark thresholds are versioned experimental targets, not claims already achieved.
