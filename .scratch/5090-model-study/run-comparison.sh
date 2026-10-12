#!/usr/bin/env bash
# Run on MONSTER-GAMING-PC after copying the study scripts and downloading models.
set -euo pipefail
study_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
profile="${1:?Usage: run-comparison.sh bonsai|qwen|flash|vllm [context] [cache] [batch] [rope-scale]}"
context="${2:-32768}"
cache="${3:-f16}"
batch="${4:-256}"
rope_scale="${5:-1}"
run_id="${profile}-$(date -u +%Y%m%dT%H%M%SZ)"
exec 9>"${study_dir}/benchmark.lock"
flock -n 9 || { echo 'Another comparison owns the GPU test lock.' >&2; exit 1; }
trap 'python3 "${study_dir}/profiles.py" restore' EXIT
launch=(python3 "${study_dir}/profiles.py" "$profile" --context "$context" --cache "$cache" --batch "$batch" --scale "$rope_scale")
client=(--port 18000 --container '')
if [[ "$profile" == vllm ]]; then
    launch+=(--graphs)
    if [[ -n "${STUDY_KV_CACHE_BYTES:-}" ]]; then
        launch+=(--kv-bytes "$STUDY_KV_CACHE_BYTES")
    fi
    client=(--port 18000 --container benchmark-5090-server)
else
    client+=(--llama)
fi
"${launch[@]}"
python3 "${study_dir}/benchmark.py" "${client[@]}" --label "${run_id}-smoke" --out "${study_dir}/results" --speed --quality --agents
python3 "${study_dir}/humaneval_benchmark.py" "${client[@]}" --label "${run_id}-humaneval"
python3 "${study_dir}/humaneval_benchmark.py" "${client[@]}" --label "${run_id}-thinking" --thinking
context_timeout=900
if [[ "$context" -gt 524288 ]]; then
    context_timeout=7200
elif [[ "$context" -gt 262144 ]]; then
    context_timeout=2400
fi
python3 "${study_dir}/context_stress.py" "${client[@]}" --label "${run_id}-context" --sizes "$context" --seeds 1,2 --timeout "$context_timeout"
docker logs benchmark-5090-server > "${study_dir}/${run_id}.log" 2>&1
