# Document rig harness handoff

Prepared only; no model calls or rig execution. Script `.scratch/autonomy/qualify-documents.py` SHA256 `efb7e5734c2bd84ec25c55791b850128161932b90cece577cc9941739b1d5890`. Syntax compilation/help checks pass. Candidate repairs remain ongoing: supply the final frozen candidate manifest/hash, not the earlier candidate.

Example, executed by root on the rig from its isolated trusted candidate checkout:

```sh
python3 .scratch/autonomy/qualify-documents.py \
  --repo /absolute/isolated-candidate \
  --candidate /absolute/final-candidate.json \
  --candidate-sha256 FINAL_MANIFEST_SHA256 \
  --contract /absolute/rig-trial-contract.json \
  --contract-sha256 41c257bcb0a2ed955dffa047c75b0dcef3712a88eab8fb1bd0a8a3a516fc846e \
  --config /absolute/existing-private-config.json \
  --serving-container gflo-model \
  --expected-serving-id EXACT_RUNNING_CONTAINER_ID \
  --expected-serving-image sha256:EXACT_SERVING_IMAGE \
  --output /absolute/new-trial-directory \
  --run
```

Flags require actual values. No `--run` means no action. Existing output refuses overwrite. The harness verifies source/contract hashes, exact container/image identity, alias, context and KV cache before and after; handles separated or attached short options and long `--name=value`. It records selected nonsecret serving fields plus argv hash, never full argv/environment/private config. Endpoint model/props reads check alias/context and are not answer calls.

Fresh acquisition precedes two answer attempts, one per frozen question without retries. Unsupported expectation `insufficient` maps to `insufficient_evidence`. A trusted ModelWorker subclass records question-specific request hash/effective limits and decoded raw response in the actual answer child before answer validation; invalid JSON content/citations remain inspectable. No authorization/config is recorded. Existing 120s and 65536-byte client response bounds remain unchanged; a rare expanded decoded representation records a bounded prefix plus full digest/size. Failed network/oversize response cannot create complete raw output the client never returned.

Replay runs saved successful IDs in a fresh pinned Python3.12.13 runc container with network none, no config/key mounts, only trusted gflo package RO and owned store RW (lease needs writes). Record hashes excluding `.lock` must remain unchanged; answers/provenance must match except current age. Failures persist in receipt and per-question artifacts. Any failed status exits nonzero; successful structure is explicitly semantic-pending. Root's separate rig lifecycle probes and independent actual-answer semantic review remain required.
