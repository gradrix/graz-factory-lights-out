# Factory context

Vocabulary for prepared, bounded software work and its evidence.

## Language

**Factory**: The system that coordinates software work, validates results, and retains evidence.

**Control plane**: The trusted authority that owns work state, policy, validation, and acceptance.

**Work atom**: A bounded, independently restartable unit of work with declared inputs, scope, outputs, gates, and a finite retry budget.

**Attempt**: One execution of a Work atom under a specific lease, retaining its observations and outcome.

**Lease**: A temporary grant to advance an Attempt that fences results after it expires or is replaced.

**Attempt worker**: The participant that proposes changes using a bounded view and granted tools, without authority to accept its own work.

**Model turn**: One bounded inference request within an Attempt.

**Candidate**: An immutable proposed result awaiting independent validation.

**Gate**: A mandatory independent check against a pinned validation contract.

**Gate receipt**: Retained evidence of a gate outcome bound to the exact work, inputs, and candidate.

**Acceptance**: A durable decision that a candidate satisfied its required gates against the declared current inputs.

**Acceptance finding**: Later contradictory evidence bound to an accepted candidate that blocks its reuse while preserving historical acceptance.

**Prepared integration**: Combining accepted contributions against a shared pinned base and validating the combined candidate independently.

**Upstream contract**: A pinned provider interface or behavior specification on which a consumer's work depends.

**Quarantine**: The terminal state of work that exhausted its permitted attempts without acceptance.
