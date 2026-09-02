# Domain Context

## Factory

The autonomous system that turns a product intent into validated source code and durable evidence. A Factory may pause or escalate when it cannot satisfy its acceptance model without violating a boundary.

## Intent package

A versioned, traceable statement of product intent, assumptions, constraints, and acceptance criteria. The Factory may derive an Intent package from a natural-language request before execution begins.

## Work atom

A small, independently restartable unit of Factory activity with bounded context, declared inputs and outputs, validation, and a finite retry policy.

## Product module

A cohesive unit of generated product code with a narrow public contract, explicit dependencies, local validation, and a bounded comprehension footprint.

## Capability profile

An explicit declaration of a technology stack or activity the Factory knows how to operate and validate. Unsupported capabilities are not silently improvised.

## Acceptance model

The collection of executable criteria and product-level scenarios that determines whether generated work satisfies the Intent package.

## Evidence gate

A transition rule that advances Factory work only when required deterministic evidence exists. Model judgment may supplement but does not replace deterministic evidence where deterministic verification is possible.

## Product graph

The navigational representation of Product modules, their contracts, and their dependencies. It helps an agent select authoritative source evidence without treating generated summaries as truth.
