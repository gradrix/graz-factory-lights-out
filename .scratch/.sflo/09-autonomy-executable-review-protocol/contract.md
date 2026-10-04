# Executable review protocol successor

Agent-defined repair under continuing user authorization. Predecessor: ../09-autonomy-executable-review/contract.md SHA256 1fe3c4763dd4e1ee6d3b280619dcbce4ac1814d7253dbbba5c1d8d6f47f959d1. Inherit its objectives, four frozen known-case fixtures, order, acceptance, isolation, source validation, lifecycle, serving/environment identity, evidence and no-promotion boundaries except the explicit changes below. Initial trial remains failed and immutable.

## Isolation

New worktree /home/gradrix/repos/gflo-review-protocol-prototype, branch prototype/review-protocol-20261004, base37b7f1d1416d5497ca38291b47b364882d2d44ef. Maintained gflo and prior planning/cancellation helpers stay byte-identical. Reuse public fixture manifest05de766048d96216865b8e5d0c817166ac1635391a6ed496b9ce6c3b0b6bdb37 unchanged, including its original provenance/contract metadata. Private expectations remain excluded. New trial output/admission only.

## Two phases within unchanged total budget

Eight total charged attempts, twelve commands,300seconds work,150seconds cleanup per case. Exploration lasts at most180seconds from work start and consumes at most seven attempts. Every exploratory request/command deadline is bounded by this phase deadline and existing individual caps. Finalization uses the remaining overall work time, at most120seconds per request, and exactly one separately charged request with no tools and response_format={"type":"json_object"}. Never reset overall work/debit counters. Phase transitions and recovery are durable evidence.

An exploratory response without tool calls triggers finalization; its prose/JSON is untrusted context, never a verdict. Reaching seven attempts, twelve commands or the exploration time boundary also transitions if at least one command is attested and overall time remains. At least one positively attested command is mandatory. Final response must pass strict JSON parsing and existing review.validate, have no tool calls and no length truncation. Invalid final output is terminal incomplete; no fence stripping, embedded JSON extraction or final retry.

One recovery is eligible only for an exploratory response with finish_reason=length. Retain raw response and charged cost, execute zero commands from its entire batch, and add short controller feedback asking for one compact valid call within remaining limits. Do not put malformed tool calls into API history or fabricate tool responses. A second truncated response is terminal incomplete. If phase/request capacity has already ended, finalize from existing actual evidence without another exploration request. Unknown tools, authority/schema violations in nontruncated responses, transport/lifecycle failures, missing start/cleanup proof, changed source or cancellation remain terminal. No ninth request and no budget replenishment.

Neutral instructions explain phase limits, truthful finite-probe coverage, and programmatic generation of large/repetitive data instead of long literals. No case-specific hint. Commands remain read-only/offline, with fresh scratch for each invocation. All existing bounded raw capture and source-as-data rules remain.

## Gates

Before real inference: independent controls for phase reservation, separate JSON final transport with no tools, no ninth attempt, truncated multi-call zero execution and exactly one eligible recovery, malformed final refusal, no-attestation refusal, phase/overall deadline and cancellation publication fences. Reuse byte-identical executor/lifecycle evidence explicitly; run a synthetic actual-rig vertical proving new phase wiring without model calls. Freeze candidate, tests, inputs and admission before the once-only four-case repeat.

Independent semantic acceptance remains all four correct grounded classifications, with no invented blocking requirements or unexecuted-test claims. Account all failures/costs; preserve initial and successor results separately. Passing permits only a fresh-case qualification decision, not maintained promotion or general reliability claims.
