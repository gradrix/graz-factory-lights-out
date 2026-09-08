# Bounded execution and trusted process gates

`DockerBroker` runs small Python source bundles in disposable local containers. `run_gate` checks their observable process behavior against a controller-owned `ProcessGate`, using a fresh validation container for every case. Expected outputs and the canonical validator plan remain outside the container. Candidate smoke execution uses another container. This is the first Python process-contract capability, not a general shell/build/package-install platform.

The caller supplies an installed, immutable Python image identity. The broker never pulls images. It resolves and pins a local Unix Docker endpoint, rejects image-declared volumes, serializes execution per artifact store, and checks ownership labels before cleanup. No repository directory, ledger, artifact directory, validator directory, credentials, Docker socket or GPU is mounted/passed into a candidate. There is no network. Only validated text files, a trusted command and explicit stdin enter the container. Model-generated requests must still be authorized by the forthcoming worker/tool layer; the broker API itself belongs exclusively to the Control plane.

Each container runs as UID/GID 65534 with dropped capabilities, no-new-privileges, seccomp, private namespaces, a read-only root, 128 MiB memory with zero extra swap, 32 PIDs and one CPU. Workspace/tmp are bounded tmpfs mounts. The trusted bootstrap checks effective cgroup/security settings before executing candidate code. `qualify()` must first demonstrate real memory/PID enforcement on this host; missing controls fail closed. These choices follow Docker's [resource constraint semantics](https://docs.docker.com/engine/containers/resource_constraints/). The Docker daemon remains trusted host authority; this is ordinary container isolation, with the [shared-kernel limitations](https://docs.docker.com/engine/security/) that entails.

Bundles contain at most 100 normalized text-file paths and 256 KiB of serialized content. Paths cannot escape or overlap as file/directory prefixes. Candidate processes receive up to 64 KiB stdin, a deadline up to 60 seconds, and at most 1 MiB combined captured stdout/stderr. Container logging is disabled so output floods cannot grow daemon log files. The host capture client enforces the byte budget; timeout/output overflow stops the container. Capture detaches before kill to avoid Docker blocking while draining a full output pipe. No mutable workspace is exported: code changes must be published as a new bundle through the controller. Binary files, dependency installation and general repository checkout/export are not supported by this initial capability.

A successful execution produces an immutable `Execution` record containing the exact candidate digest, image/container identities, command/stdin, exit code, OOM flag, elapsed time and base64-encoded output. Failed/interrupted operations retain diagnostic artifacts. Every operation cleans up its owned container in `finally`; after controller process death, `reconcile()` removes stale containers belonging to the same store under its exclusive lock. SIGINT during actual execution is tested. SIGKILL/power loss cannot run cleanup; startup reconciliation is required, and unattended supervision/SIGTERM handling belongs to the controller integration stage.

`ProcessGate` binds one or more command/input/expected-output cases into the Work atom's `validator_digest`. The gate runner checks the live Lease and plan binding, executes against the stored candidate, and independently compares captured stdout and exit status. Candidate nonzero exit, wrong output, timeout, output overflow or OOM yields `fail`; Docker/bootstrap/evaluator errors yield `inconclusive`. Exit 125 is reserved for bootstrap failure and conservatively treated as evaluator failure. Neither failure type can satisfy acceptance. An exact passing receipt binds the contract, inputs, candidate, plan and retained evidence. Generated code printing a generic success marker does not override those comparisons. Test adequacy remains the trusted plan author's responsibility.

The gate report embeds the full trusted plan and execution observations. Its qualification digest references retained target-probe evidence; the artifact store does not garbage-collect anything. Gates do not update a source tree, infer authoritative input changes, enforce a proposed edit's path scope, or dispatch/retry model turns. The worker/result validator and durable loop must provide those pieces before the twelve-task pilot.

Run deterministic checks with `.venv/bin/python -m pytest -q`; eight Docker tests skip unless explicitly enabled. Run all checks on this qualified host with a fresh evidence directory:

```sh
GFLO_BROKER_TEST_IMAGE=python@sha256:ae52c5bef62a6bdd42cd1e8dffef86b9cd284bde9427da79839de7a4b983e7ca \
GFLO_BROKER_EVIDENCE=.gflo/evidence/broker-new-run \
.venv/bin/python -m pytest -q
```

The evidence directory retains a test ledger and immutable objects; choose a new directory per run. The live tests execute bounded OOM/PID probes, demonstrate clean candidate/validator separation, check host/credential/network exclusion, exercise timeout/output floods and SIGINT cleanup, reconcile stale owned containers, and accept a candidate through real process gates with reopen verification. They do not call the model or qualify general coding ability.

## Gate execution-report validation

`python-process-gate-v2` verifies broker qualification and revalidates every execution
report before scoring. Candidate digest, command, stdin, validation purpose and
resolved image must match the requested case. Container IDs must be nonempty and
cannot repeat within a gate. Output encoding is strict base64, combined decoded
output is bounded, and elapsed time must be finite and nonnegative. Malformed or
mismatched reports are inconclusive with retained diagnostic evidence; matching stdout
alone cannot authorize acceptance. Explicit model-like success JSON in stdout is
ordinary candidate output and fails when it differs from the trusted expectation.

These are checks on returned broker evidence, not permission for workers to call the
trusted ledger API. Earlier v1 receipts retain their historical identity; they are not
silently rewritten as v2 qualifications.
