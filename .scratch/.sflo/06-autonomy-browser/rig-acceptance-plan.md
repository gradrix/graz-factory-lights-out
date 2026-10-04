# Unit06 rig acceptance harness — prepared, not executed

Status: syntax checked only. No rig, Docker, or model calls were made in preparing this harness. Source repairs are active; c201083/v2 remains blocked by security B1–B4. Execution requires a new frozen candidate manifest and coordinator go. No qualification result is implied.

## Entry point

`rig-acceptance.py` runs the existing five-control/five-mutant driver, then bounded supplemental controls and `rig-lifecycle.py`. Both files must be staged alongside the frozen checkout. Supply absolute paths; the output must not exist.

```sh
python3 .scratch/.sflo/06-autonomy-browser/rig-acceptance.py \
  --repo "$FROZEN_REPO" --candidate "$FROZEN_MANIFEST" \
  --candidate-sha256 "$FROZEN_SHA256" \
  --fixture "$FROZEN_REPO/evaluations/local-browser" \
  --fixture-sha256 20d07c59c1af28f5728847179406560787b579b86c20c030e30032492f16ac10 \
  --support-store /home/gradrix/gflo-browser-c201083/.gflo/browser-support \
  --support-id df4755523d7682b461c222f22f99453346eccef769f6bbc096ac77772a8ffd20 \
  --original-seccomp "$FROZEN_REPO/.scratch/autonomy/browser-boundary-prototype/seccomp.json" \
  --output "$FRESH_OUTPUT" --run
```

The original seccomp file must be staged unchanged and match `cc3e61cabda6bbc1e53e54d27ba4d55a9d3be829b6dd1a596f4a7b31b1cc7849`. The harness copies validated support into its own stores; it does not prepare again or mutate the source store. The model service is outside this experiment: no inference, configuration, restart, or uptime assumptions.

## Evidence and discrimination

| Control | Evidence type and requirement |
|---|---|
| Five flows plus five semantic mutants | Existing driver, actual containers; exact source/fixture/support hashes before/after; mutants must fail journey phase; all-context trace and PNG audit, saved inspect |
| Sandbox/shm and gateway/LAN/public IPv4/IPv6 | Actual helper facts from exactly five positive receipts; nonzero samples/peak, renderer user namespace and seccomp, forbidden launch flags absent, every denial disconnected |
| Hostile page text | Actual page content remains inert; successful screenshot journey |
| Redirect/private port and WebSocket | Actual owned primary/secondary servers; copied trusted helper reads final independent `/hits` in `finally`; require exactly zero AND a policy failure, never accept an assertion failure as proof |
| Public redirect/navigation, download/upload, event flood | Actual browser attempts and failed result with confirmed cleanup; inspect failure reason in final review |
| Full journey deadline, app death | Actual pending journey / owned app exits; deadline elapsed bounded 55–130s including cleanup |
| Original seccomp | Exact original profile selected only in private executor spec; actual sandbox launch must fail |
| Version mismatch | Explicit controlled seam: copied helper expects impossible Node version; real container must reject with mismatch; this does not simulate an independently installed wrong image |
| Artifact corruption/extra byte | Controlled transport mutation after a real pair completes; receipt must reject |
| Artifact cancellation | Copied-helper barrier before finalization; actual cancellation/removal, failed result |
| Owner death | Actual SIGKILL after first observed running app, separately after explicit artifact barrier; exact labeled containers removed, no new receipt, prior actual passed result unchanged and inspectable after cleanup |

Raw receipts, requests, copied fault helpers, results, and subprocess logs remain under the fresh output. Any failed assertion is preserved. Helper adapters require an exact unique source anchor and stop if the final interface changes; re-review adapters against the final frozen candidate before running.

## Complementary repair gate (no redundant broad suite)

The final security review must separately bind B1 final-publication cancellation, B3 bounded daemon logging, B4 uncertain create/cleanup fencing, plus approved input/support tamper rejection to the repaired candidate. Reuse its focused controlled probes; do not rerun old scripts that silently activate c201083. Those are controlled seams, not evidence of an actual Docker daemon outage. A successful harness alone cannot close those blockers. Final acceptance joins its results with that candidate-specific security report and the ordinary CLI/offline inspect evidence. Startup owner-death observes the first running app; its receipt must record the exact names and observed phase, without claiming an unobserved daemon-internal timing point.

The coordinator should stop on any unexpected outcome, preserve output, and return to the builder. No source edits or silent fixture revisions during qualification.

Prepared script SHA256: `rig-acceptance.py` = `93a04830328aacb3ff49e7b24e1189dc4c9a53d04607ca00e866434082c2f81d`; `rig-lifecycle.py` = `92b010d8c243a323d8293e785f689fc69955dbe842da3ae089dbec731525f4e5`.
