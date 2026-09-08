# Acceptance findings

A trusted control-plane operation records contradictory evidence against the exact
accepted atom contract and candidate. It appends an event; historical acceptance,
Attempts and passing gates remain immutable. Status/history expose the finding and
whether acceptance has been challenged. Acceptance replay and prepared integration
must reject the challenged result. Repair produces a new atom/candidate with new gates.

Use the existing immutable event store. On the first finding, raise the ledger's
minimum reader version to 3 within the same transaction. Older controllers must fail
to open such a ledger instead of ignoring the finding and returning accepted again.
New readers continue to support unchallenged version-2 ledgers.

The finding binds atom, contract, candidate, a nonempty bounded reason and a verified
artifact containing contradictory evidence. Identical delivery is idempotent. Missing
or corrupt finding evidence appears in artifact audit; its loss never re-enables reuse.
There is no automatic dismiss/clear operation in this slice. Findings are local to
this ledger; automatic propagation across separately exported products is unsupported.

Qualify retained history, replay/integration rejection, wrong bindings, invalid evidence,
reopening, duplicate delivery and concurrent finding/acceptance serialization. Record
real campaign findings only after the frozen scoring and supplemental review finish.
