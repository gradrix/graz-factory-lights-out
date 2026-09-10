# Qualify ai-gamer winner detection on a real repository

Type: task
Status: resolved

## Selection and verified problem

Owner offered leds-service or ai-gamer and delegated target/task choice. Choose
ai-gamer at 7ccbb585a6097e85416fb109ff5d03a92ce09b88: hardware-independent game rules
permit independent deterministic checks without TensorFlow training or GPIO devices.
leds-service remains a later hardware/service-integration target.

The original TikTakToe reports X winning for separated pieces at (0,0),(2,0),(4,0)
on a 5x5 board with line length 3, and misses a contiguous anti-diagonal at
(2,4),(3,3),(4,2). Both observed locally before editing source.

## Prospective qualification

Use the local factory single planner and pinned independent policy to fix winner
window scanning and add regression tests. Preserve public interfaces, gameplay and
all unselected files. Validate contiguous horizontal, vertical and both diagonal
windows on rectangular boards; accurately determine whether a future winner is
still possible. Compare independently generated boards against a trusted window
reference, reject gapped false wins, preserve board bytes, and run newly generated
regression tests against candidate and original baseline. No game server/GPU training
is needed for this rule-only task. Retain failures and any factory changes needed.
Deliver the selected candidate as a reviewable target branch; do not claim training
quality or full-system qualification from rule tests.

## Answer

Delivered [merged PR 1](https://github.com/gradrix/ai-gamer/pull/1), commit 0011cd6.
Local implementation passed the full winner oracle on its second 12K/6K low-reasoning
attempt. All local test-generation trials halted; Codex wrote 17 passing regression
cases. The same final oracle and baseline-rejection checks passed on the exported
checkout. All 86 other original files survived, including the SQLite database.

This qualification exposed a boundary, not an end-to-end factory success. The task
and oracle were prepared; failure feedback exposed reference code. Retained results
include every failed profile/trial, incomplete server usage, and reviewer attribution.
The original legacy gameplay test cannot collect due to stale models imports; no
training, service integration or million-line capability was qualified. Follow up on
worker read/turn budgeting before another product trial.
