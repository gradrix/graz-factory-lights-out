# Fresh-start delivery

Accepted initial release. No active or unclaimed mutation unit remains.

1. [Local model service](delivery/01-model-service.md) — accepted: Flash 128K/Q4 active, short warmed decoding ~95 tokens/s, rollback tested.
2. [Minimal factory loop](delivery/02-factory-loop.md) — accepted: CLI, isolated work, immutable checks, bounded repair/recovery, independent QA and coverage.
3. [Real tasks and release checks](delivery/03-real-pilot.md) — accepted: three representative projects, preserved initial review failures, model-driven repairs and final semantic recheck.

[Release manifest](evidence/release.json) · [Pilot results](../../docs/pilot-results.md) · [Decision map](map.md)

Next potential increment: evaluate a small independent local patch-review assignment against the observed defects. It is not implemented or silently treated as accepted. Large-project autonomy and automatic integration remain outside this release.
