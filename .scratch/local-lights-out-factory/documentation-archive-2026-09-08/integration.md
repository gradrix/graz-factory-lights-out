# Prepared integration

`gflo integrate` combines pinned accepted Work-atom outputs from one exact source
base, validates the combined source in clean Docker containers and accepts an
immutable artifact. It checks current base and provider-contract identities before
admission, validation and acceptance. It rejects overlapping edits and stale
consumers; it does not ask a model to resolve conflicts implicitly.

```sh
gflo --db RUN/ledger.db integrate RUN/integration-plan.json --current-state RUN/current-state.json
gflo --db RUN/ledger.db history integration
```

The current-state file is trusted control-plane input. The caller must update it
when the product base or provider contracts change. Checks are not an atomic Git
compare-and-swap: this command does not modify a checkout or promote a revision.

An IntegrationPlan pins each child's atom contract and accepted candidate, the
common base, current provider contracts, mandatory ProcessGates and broker image.
Each child must have a prepared RunPlan; recursively integrating IntegrationPlans
is not supported yet. All changed paths must fit both child and integration scopes.
Every combined gate is mandatory even when all child gates passed.

Rerunning the same command resumes retained validation and reuses completed gate
receipts. Accepted reruns reverify artifacts and preserve one acceptance. Failed
validation retains its evidence; semantic repair requires new prepared work.

Worker context policy `bounded-python-v3` includes up to sixteen distinct UTF-8
contract excerpts, each at most 16,384 characters, keyed by verified artifact hash.
The normal exact tokenizer budget also applies. Excerpts are untrusted task data
and cannot grant file access, tools or authority. Missing or corrupt contracts
prevent submission/acceptance and appear in artifact audits.

Live fixture: `scripts/check_integration.py --output NEW_DIRECTORY`, using the
qualified local graph-serving profile and pinned Python broker. The first retained
run is `.gflo/evidence/prepared-integration-live-v1/`: one provider and two consumers
accepted on their first attempts; independent combined gates produced 42 and 84.
This small fixture qualifies the prepared integration boundary, not large-project
planning, automatic repair or Git promotion.
