# Local operation

## Installed model

`gflo-model` on MONSTER-GAMING-PC serves the tested **ISTA-DASLab Flash-Next GSQ-RCO Coder export**, using the downloaded two-part GGUF and llama.cpp b11284. This is a pruned Coder export, not the complete official Flash model.

Current default: 98304 context, Q4 K/V cache, batch and microbatch 512, one slot. Model files and runtime are under `/home/gradrix/benchmark-5090/flash`. The CUDA image is pinned by image ID in `ops/model.py`. No downloads occur on startup (`--pull never`, model `--offline`). A configured context includes instructions, input, reasoning and output; reserve space for the response.

The endpoint is authenticated and bound only to `127.0.0.1:18000`. Its key lives at `/home/gradrix/.local/state/gflo-model/api-key` with mode 0600. Do not put the key in Git or command-line arguments. `unless-stopped` restarts the container when Docker restarts. The original `local-vllm` container is preserved, stopped, with automatic restart disabled to avoid GPU contention.

From the rig:

```sh
python3 /home/gradrix/gflo-runtime/ops/model.py status
python3 /home/gradrix/gflo-runtime/ops/model.py up
# Alternative measured profile; stops/replaces only GFLO's model container:
python3 /home/gradrix/gflo-runtime/ops/model.py up --context 65536
# Restore the original container and its original restart policy:
python3 /home/gradrix/gflo-runtime/ops/model.py rollback
```

`up` defaults to 96K/Q4; 64K uses Q8 unless `--cache-type q4_0` is supplied. The 128K/Q4 profile remains available with `--context 131072`. At the current rig load, the fixed 16.9K prompt decoded at about 74 tokens/s on 96K versus 16.5 on 128K. Fresh API and TypeScript trials passed with independent semantic review; larger-project reliability remains unqualified. Loading takes time and can evict host file cache. Replacing the model disrupts active requests, so change profiles only when runs are idle. Failed setup restores original vLLM automatically for caught failures; after abrupt process/host death, inspect status and run the explicit rollback if needed.

The rollback was tested against original container/image/command/environment/mount/port identities and an authenticated generation. `up` never edits the separate `ai-playground` configuration or deletes original cache volumes.

## Use this checkout remotely

Create `.gflo`, copy the private key through SSH, and forward only the model port:

```sh
mkdir -p .gflo
chmod 700 .gflo
scp monster-gaming-pc.lan:/home/gradrix/.local/state/gflo-model/api-key .gflo/model-key
chmod 600 .gflo/model-key
cp config.example.json .gflo/config.json
ssh -N -L 127.0.0.1:18080:127.0.0.1:18000 monster-gaming-pc.lan
```

Keep that SSH terminal open. In another terminal, `python3 -m gflo doctor`. Host-key checking remains enabled. Do not expose this endpoint publicly.

On the rig, configure `.gflo/config.json` with endpoint `http://127.0.0.1:18000` and `api_key_file` set to the absolute private key path above. No SSH tunnel or second machine is needed for local execution.

## Sandbox image

The qualified default profile uses locally installed Python 3.12.13 image ID:

```text
sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc
```

Its publisher reference is `python@sha256:3d5ed973e45820f5ba5e46bd065bd88b3a504ff0724d85980dcd05eab361fcf4`. Preparing another machine may require a one-time download, or transfer it from the rig without accessing a registry:

```sh
ssh monster-gaming-pc.lan 'docker save python@sha256:3d5ed973e45820f5ba5e46bd065bd88b3a504ff0724d85980dcd05eab361fcf4' | docker load
```

The configured local image ID works after that transfer. Use a newly pinned prepared image for additional dependencies; the factory will not install them on demand.

## Recovery and retention

Run `status` first, then `resume RUN_ID`. Pending model requests are not replayed as trusted results. An interrupted attempt consumes its allowance, leftover workspace containers are stopped, and a new attempt receives the retained files and interruption evidence. A completed saved verdict is reconciled only when candidate identity matches. A model response the server cannot parse as a tool call (a truncated or self-repeating call; llama.cpp answers HTTP 500 "Failed to parse tool call") is not an interruption: the worker asks for a shorter call, and after two more such responses it ends the attempt, which then fails verification as usual. A review timeout likewise fails the attempt. Other model server errors still interrupt the run.

Keep `.gflo/runs` together: SQLite, acceptance snapshots, private Git snapshots and artifacts form one recoverable set. Do not edit an active run. To change the requirement or exhausted budget, create a new task/run. No automatic cleanup removes old evidence; archive old run directories and their database together when desired.

## Observe and control a run

```sh
python3 -m gflo watch RUN_ID
python3 -m gflo watch RUN_ID --once
python3 -m gflo serve --port 8787
python3 -m gflo cancel RUN_ID
python3 -m gflo resume RUN_ID
```

Open `http://127.0.0.1:8787`. For the rig, forward its loopback port with
`ssh -N -L 8787:127.0.0.1:8787 monster-gaming-pc.lan` after starting the observer there.
The page and API are read-only; cancellation/resume are CLI operations. No model configuration is needed to observe. The API lists the newest 100 runs; a specific run remains addressable. Events have a version and increasing cursor: `/api/runs/ID/events?after=SEQ` returns at most 500 records. Reconnect using the last received sequence.

The page shows attempts and their limits, current operation, heartbeat and elapsed time since meaningful progress. A model response taking over 30 seconds is marked slow, not declared deadlocked. There is no estimated completion percentage. An abruptly killed runner is displayed as interrupted by checking Linux process identity, rather than trusting its last SQLite status. Resume retains the workspace and consumes the original remaining attempt budget. Accepted runs remain terminal and their artifacts are checked for changes.

Cancellation sends SIGINT only to the recorded Linux process identity via a pidfd; it does not kill unrelated runs. Each container has a separate guardian that removes it when the runner's ownership pipe closes, including SIGKILL. Docker daemon availability is required for cleanup; resume requires cleanup before inspecting/accepting retained work. Linux `/proc` and pidfds are required by these controls.

Public evidence is limited to patches, worker summaries, verification and interruption receipts. Downloads are capped at 1 MiB and marked when truncated. Raw model trajectories and task/config files are not served. Common bearer/password/key/token patterns are redacted; this is defense in depth, not a general secret detector. Keep source and tasks free of credentials. Trajectory records are capped at 256 KiB each and approximately 64 MiB per attempt; oversized records are replaced by explicit truncation receipts. Durable events contain bounded operation metadata, not prompts or command output. No automatic deletion of run history occurs.

## Worker navigation aids (opt-in)

The `navigation` key of the factory config enables aids measured in roadmap phase 2; without it the worker behaves as before. `handoff`: after each attempt one extra request (at most 120 s, which can extend the 30-minute attempt budget) asks the worker for up to 4,000 characters of notes (files, functions, what changed, next step) that the next attempt receives as its own findings. `checkpoint: N`: after N turns with no file changed (test-run caches such as `.pytest_cache` do not count), the worker is asked for a short plan and to start editing. `max_turns`: overrides the task turn budget (1–100; the 30-minute attempt budget still applies). `map`: offers a `map(query)` tool, `gflo/recipes/repo_map.py` run read-only in the sandbox, listing modules, signatures with line numbers, importers, and definitions and usages of a name (Python profiles only, output at most 16,000 bytes). `stale_tests`: tells the worker to update existing tests that assert behaviour the task deliberately changes. `ops/delivery/drive.py` names arm combinations (`notes`, `plan`, `map`, `nav`).

## Independent review and unresolved product choices

New CLI runs require fresh-context local review after executable checks pass. `review_required` is frozen in `task.json`; historical runs keep their original scope. A task author may explicitly set it to `false` for a checks-only experiment, which does not qualify reviewed delivery. A required reviewer cannot silently disappear on resume.

The reviewer receives the objective and the complete candidate when it fits 200,000 source bytes / 1,000 files, with no tools or writable mount. A larger project is reviewed through the files the candidate changed, as computed by the controller; when those exceed the bounds too, changed files are shown as exact-line windows of 40 lines around each changed hunk, with unchanged lines blanked so line numbers stay exact. When even that does not fit, the attempt fails reviewability visibly. Its findings identify source locations, severity, concrete evidence and requested repair. Missing/malformed/contradictory review stops the run. A blocking review returns evidence to the worker for repair, then checks and review repeat. Review alone cannot establish acceptance. Accepted receipts hash both verification and review artifacts; changing/removing them invalidates reported acceptance.

The qualified profile uses medium reasoning for coding, with a requested 1,024-token thinking budget inside a 4,096-token output limit. Fresh review uses the same token limits with a 600-second request timeout for patch review; a timeout fails the attempt rather than the run. The installed llama.cpp profile completed the recorded qualification; actual reasoning-token consumption is not reported separately, and arbitrary OpenAI-compatible servers are not assumed to honor this extension. See the delivery map and qualification evidence for remaining review and documentation limitations.

A worker can call `question` for a consequential missing product decision; a reviewer can also return `needs_input`. The run stops with its question and retained evidence. Repeated `resume` does not invent an answer or spend another attempt. Resolve the product choice in a new explicit task contract and create a new run; an in-place answer/revision API is not implemented yet.

### Project regression checks

The current Python stdlib sandbox runs `python -B -m unittest discover -s tests` whenever the candidate contains a `tests/` directory, in addition to the immutable external acceptance commands. Both run read-only and offline with bounded execution. A failing generated test blocks acceptance and returns its output to repair; a model's claim that its tests passed is not evidence. External acceptance and fresh review are still required. Other stack profiles must supply their own test execution when introduced.
