# Local model serving

The measured factory profile is [vllm-5090-graphs.example.json](vllm-5090-graphs.example.json):
RTX 5090, pinned Inferact/Qwen3.8-27B-NVFP4 checkpoint and vLLM image, graph execution,
16K server context, BF16 KV cache, and one serialized request. The worker normally
uses an 8K budget including a 2K output reserve. See [evaluation](../../docs/evaluation.md)
for measured capability and limits.

## Inspect and start

The launcher is a standard-library Python script. Managed mode requires Linux,
Docker with NVIDIA GPU support, the pinned image, and a populated model cache.
Run from the repository root:

```sh
python3 scripts/serve.py config --config infra/serving/vllm-5090-graphs.example.json
python3 scripts/serve.py doctor --config infra/serving/vllm-5090-graphs.example.json
python3 scripts/serve.py up --config infra/serving/vllm-5090-graphs.example.json
python3 scripts/serve.py smoke-test --config infra/serving/vllm-5090-graphs.example.json
python3 scripts/serve.py status --config infra/serving/vllm-5090-graphs.example.json
```

The graph profile starts `gflo-vllm-graphs` on `127.0.0.1:30000`, served model
`gflo-local`. It requests 36 GiB host RAM, three CPUs, 1024 PIDs, and GPU 0.
It uses the named volume `local-vllm-huggingface-cache` in offline mode. An empty
volume cannot serve the model: download the exact configured checkpoint and
supporting tokenizer/config files into a compatible Hugging Face cache first.
Fresh-host cache provisioning is not yet a verified turnkey installation path.

Use `down` with the same configuration to stop the managed service. Copy example
configuration to an ignored `*.local.json` for local overrides; regenerate prepared
plans after changing deployment settings. The launcher checks managed ownership
before removal. Inspect its `config` output before allocating GPU/host resources.

## Other profiles

[vllm-5090.example.json](vllm-5090.example.json) retains the earlier eager profile;
[sglang-5090.example.json](sglang-5090.example.json) retains the comparison profile.
They are not the selected graph deployment. Configuration files pin the exact
images, checkpoints, and engine options; do not silently replace them when comparing
results. The factory client currently targets vLLM's verified chat/tokenizer behavior.

[external.example.json](external.example.json) describes an already-running service;
[managed.example.json](managed.example.json) illustrates launcher configuration.
The general serving launcher and the factory model client have different boundaries:
the factory client requires numeric loopback and provides no automatic remote or
cloud fallback. Model deployment provenance is a recorded configuration binding,
not remote attestation of the weights actually served.
