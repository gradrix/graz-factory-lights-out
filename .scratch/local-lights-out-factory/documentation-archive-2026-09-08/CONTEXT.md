# Domain Context

## Factory

The autonomous system that turns a product intent into validated source code and durable evidence. A Factory may pause or escalate when it cannot satisfy its acceptance model without violating a boundary.

## Lights-out run

A preauthorized Factory run that proceeds from an accepted Intent package to Verified completion without routine human decisions or approvals. Automated isolation, evidence gates, recovery, and rollback are part of the run rather than human checkpoints.

## Preauthorization

The policies, capabilities, resource posture, and side-effect boundaries accepted before a Lights-out run begins. Actions inside that envelope proceed automatically; exceeding it is a terminal exception rather than a normal workflow stage.

## Control plane

The trusted, durable part of the Factory that owns policy, work state, evidence, credentials, scheduling, and recovery authority. Attempt workers cannot modify or impersonate it.

## Attempt worker

A disposable, least-authority execution environment for one Work-atom attempt. It may use granted tools and networks but cannot write trusted Factory state directly.

## Generation

An immutable, versioned release of the Factory. A candidate Generation is built and verified separately from the active Generation before an external launcher may promote or roll it back.

## Intent package

A versioned, traceable statement of product intent, assumptions, constraints, and acceptance criteria. The Factory may derive an Intent package from a natural-language request before execution begins.

## Work atom

A small, independently restartable unit of Factory activity with bounded context, declared inputs and outputs, validation, and a finite retry policy.

## Model turn

One bounded inference request within an Attempt. A Work atom may require several Model turns without treating their accumulated conversation as durable truth.

## Context manifest

An immutable, content-identified record of the authoritative and navigational material selected for one Model turn, including provenance, retrieval reasons, omissions, and token accounting.

## Worker view

A purpose-specific projection of a Work atom and its referenced evidence containing only what one Attempt worker needs for its responsibility. Different workers may receive different views of the same accepted facts.

## Context composer

The Factory capability that resolves Work-atom references into a bounded Worker view while preserving provenance, authority labels, required structural coverage, and output capacity.

## Context policy

A versioned, empirically calibrated rule for selecting, expanding, and budgeting Worker views for a worker type and Capability profile.

## Attempt

One immutable execution record for a Work atom, including its inputs, Lease, worker observations, outputs, evidence, and terminal outcome. Retrying creates another Attempt rather than rewriting the prior one.

## Lease

A time-bounded grant allowing one Attempt worker to execute a Work atom. Expiry makes the work eligible for reconciliation without implying that the prior process performed no side effects.

## Work ledger

The sole durable authority for Work graphs, Work atoms, Attempts, Leases, evidence references, and acceptance transitions.

## Graph revision

An immutable version of a Work graph. Re-planning appends a Graph revision and may supersede unfinished work without altering accepted history.

## Integration atom

A Work atom whose purpose is to combine accepted outputs into an accepted local revision while checking that their preconditions and Product-module contracts still hold.

## Product module

A cohesive unit of generated product code with a narrow public contract, explicit dependencies, local validation, and a bounded comprehension footprint.

## Capability profile

An explicit declaration of a technology stack or activity the Factory knows how to operate and validate. Unsupported capabilities are not silently improvised.

## Acceptance model

The collection of executable criteria and product-level scenarios that determines whether generated work satisfies the Intent package.

## Evidence gate

A transition rule that advances Factory work only when required deterministic evidence exists. Model judgment may supplement but does not replace deterministic evidence where deterministic verification is possible.

## Recovery budget

A finite allowance of attempts and resources that the Factory may spend trying to satisfy a Work atom before it must quarantine or escalate the work. Repeated attempts must incorporate new evidence or a materially different strategy.

## Quarantine

A durable non-success state that preserves a failed attempt's workspace, evidence, provenance, and dependency impact while preventing it from advancing or contaminating accepted work.

## Escalation packet

A structured request for human judgment containing the blocked decision, attempted strategies, evidence, affected Product modules, available options, and the Factory's recommendation.

## Verified completion

The state in which every mandatory requirement is linked to passing evidence, required Product-graph conformance and product scenarios pass, no unresolved escalation remains, and the accepted local revision is reproducibly buildable.

## Product graph

The navigational representation of Product modules, their contracts, and their dependencies. It helps an agent select authoritative source evidence without treating generated summaries as truth.

## Acceptance finding

Evidence discovered after acceptance that contradicts an accepted result's requirements. It blocks downstream reuse of that result while preserving the original acceptance and its history.
