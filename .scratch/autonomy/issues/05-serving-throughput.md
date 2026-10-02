# Does the 128K serving profile retain useful sustained decoding speed?

Type: prototype
Status: allocation experiment resolved; 96K/Q4 trial selected, fresh coding qualification active
Decision maker: agent, under the user's request for useful large context and local throughput

## Question

Stage3 stdlib succeeded, but its 16 coder responses had median 18.91 tokens/s, versus Stage2 D's 65.76 overall median. The stdlib prompts grew to 18,902 tokens and per-response speed fell from 46.21 to 15.02. These distributions are not an equal-input benchmark and do not establish a cause.

## Known observations

- At the original Stage3 cohort, local serving was131072 context with flash-next-coder; no serving configuration changed during that cohort.
- Live 5090 sample: 32080/32607 MiB used, 97% GPU utilization, 156.33W, 2932MHz, 43C. WSL host had about32GiB available RAM; model container about11.48GiB resident host memory. Sample is not a full utilization trace.
- Historical D context buckets are not monotonic: median74.95 at8–12K,19.78 at12–16K and69.14 at16–20K. Overall medians alone cannot distinguish workload/runtime variation.
- The frozen Stage3 batch keeps its original model/profile and budgets. No desktop apps or shared services are stopped for diagnosis.

## Experiment

After the serialized batch completes, replay a fixed synthetic short and roughly16K-token input with a fixed output budget against the current service; retain actual prompt/cache/generation timings. Repeat enough to separate warm behavior. This becomes the red-capable timing loop before ranking/testing causes. Inspect exact serving identity and aggregate VRAM state without recording credentials.

If a serving change is warranted, change one variable at a time and keep a tested return path to the current owned model service. Context reduction and KV datatype changes must be measured separately, not conflated. Preserve every failed/slow observation; do not rewrite Stage3 timings or rename a repeated task as held out.

Evidence: ../../.sflo/04-autonomy-environments/stdlib-model-metrics.json. No diagnosis or new profile recommendation yet.

## Reproduced timing loop

Executed `python3 throughput-probe.py --config /home/gradrix/gflo-runtime/.gflo/config.json --output .gflo/throughput/128k-long-before.json --shape long` on rig. Warm median16.51tokens/s at16947prompttokens; three values16.29/16.53/16.49. Short variant51tokens measured47.35warmmedian, values47.48/47.44/47.26. Both fail the predeclared diagnostic50tokens/s threshold; it is a throughput signal, not model quality acceptance. The short input minimizes the test but longer input amplifies the observed slowdown.

Ranked falsifiable hypotheses before changes:
1. Persistent serving/cache state: restarting the identical owned service will restore throughput on identical input.
2. VRAM residency pressure: reducing allocated context alone, preservingQ4KV and all otherflags, will improve identical-input throughput and reduceVRAM usage.
3. Intrinsic long-context attention cost: the long/short difference will remain after restart and allocation reduction, despite lowerVRAM usage.

First experiment: identical128K restart, then fixed-input rerun. No other desktop or shared services are touched. Each experiment preserves prior receipt and owned-service return path.

## Allocation experiment

Identical128K restart retained16.52tokens/s warm median on the16947-token prompt; persistent service state does not explain the slowdown. A prototype changes ONLY `-c` from131072to65536, retainingQ4KV and every otherDocker/modelargument; exact command-list comparison passed. 64K warmmedian74.92tokens/s. 96K warmmedian73.95tokens/s with31759/32607MiB VRAM observed aftercompletion. 128K observed32067MiB duringdecoding;64K31293MiB duringdecoding. Samples have different utilization phases and are not detailed memory-residency traces.

Measured conclusion: reducing allocated context restores identical-input throughput, reproduced at64K and96K. VRAM/WDDM residency pressure is a supported explanation, not directly proven by these counters. No inference that the model itself became smarter. 96K is the largest tested allocation retaining speed; not a proof of the absolute maximum possible. The81,441-token three-position retrieval probe passed in96.72seconds. Fresh API then accepted firstattempt in285.71seconds with73.06tokens/s median and30,021maximum prompt; independent semantic QA is pending. Fresh Node is running. Original128K service can be restored with `python3 ops/model.py up --context 131072`.

Independent serving QA: ../../.sflo/04-autonomy-environments/qa-serving-profile.md. Reproduce measured64K with `--context 65536 --cache-type q4_0`; default64K remainsQ8. The original retrieval receipt did not embed serving identity; session execution and surrounding96K launch/timing receipts associate it with that profile. This is a provenance limitation, not a claim of independent container binding. The retained retrieval probe now records and compares serving identity for future runs; the original receipt is unchanged.
