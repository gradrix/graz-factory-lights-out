# Local operation

## Installed model

`gflo-model` on MONSTER-GAMING-PC serves the tested **ISTA-DASLab Flash-Next GSQ-RCO Coder export**, using the downloaded two-part GGUF and llama.cpp b11284. This is a pruned Coder export, not the complete official Flash model.

Default: 131072 context, Q4 K/V cache, batch and microbatch 512, one slot. Model files and runtime are under `/home/gradrix/benchmark-5090/flash`. The CUDA image is pinned by image ID in `ops/model.py`. No downloads occur on startup (`--pull never`, model `--offline`). A configured context includes instructions, input, reasoning and output; reserve space for the response.

The endpoint is authenticated and bound only to `127.0.0.1:18000`. Its key lives at `/home/gradrix/.local/state/gflo-model/api-key` with mode 0600. Do not put the key in Git or command-line arguments. `unless-stopped` restarts the container when Docker restarts. The original `local-vllm` container is preserved, stopped, with automatic restart disabled to avoid GPU contention.

From the rig:

```sh
python3 /home/gradrix/benchmark-5090/gflo-model.py status
python3 /home/gradrix/benchmark-5090/gflo-model.py up
# Alternative measured profile; stops/replaces only GFLO's model container:
python3 /home/gradrix/benchmark-5090/gflo-model.py up --context 65536
# Restore the original container and its original restart policy:
python3 /home/gradrix/benchmark-5090/gflo-model.py rollback
```

`up` defaults to 128K/Q4; 64K uses Q8. Loading takes time and can evict host file cache. Replacing the model disrupts active requests, so change profiles only when runs are idle. Failed setup restores original vLLM automatically for caught failures; after abrupt process/host death, inspect status and run the explicit rollback if needed.

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

The first profile uses locally installed Python 3.11.15 image ID:

```text
sha256:a8a3e0a84b0d5fab2b3b4b32e89715a7384b7af2f81b5e82d203d12828cb2578
```

Its publisher reference is `python@sha256:ae52c5bef62a6bdd42cd1e8dffef86b9cd284bde9427da79839de7a4b983e7ca`. Preparing another machine may require a one-time download, or transfer it from the rig without accessing a registry:

```sh
ssh monster-gaming-pc.lan 'docker save python@sha256:ae52c5bef62a6bdd42cd1e8dffef86b9cd284bde9427da79839de7a4b983e7ca' | docker load
```

The configured local image ID works after that transfer. Use a newly pinned prepared image for additional dependencies; the factory will not install them on demand.

## Recovery and retention

Run `status` first, then `resume RUN_ID`. Pending model requests are not replayed as trusted results. An interrupted attempt consumes its allowance, leftover workspace containers are stopped, and a new attempt receives the retained files and interruption evidence. A completed saved verdict is reconciled only when candidate identity matches.

Keep `.gflo/runs` together: SQLite, acceptance snapshots, private Git snapshots and artifacts form one recoverable set. Do not edit an active run. To change the requirement or exhausted budget, create a new task/run. No automatic cleanup removes old evidence; archive old run directories and their database together when desired.
