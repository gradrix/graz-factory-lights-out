# Choose the first larger-system workload

Type: task
Status: resolved
Blocked by: 72, 73

## Question

What is the first larger system the owner wants the factory to build or maintain:
purpose, existing repository if any, required stack and deployment target?

## Why this decision is needed

Supervised Taskdock repair delivered a small project, but four varied original
builds yielded no fully qualified result after review. The current execution adapter
also cannot admit the factory runtime itself. The next milestone could emphasize
small-project reliability or the build/dependency path for a concrete larger system.
The intended workload determines actual dependency, build, integration and deployment
requirements; those product choices are not supplied by the existing handoff.
The owner was asked asynchronously while qualification continued. Do not infer an
answer or choose an external product architecture on the owner's behalf.

## Answer

Owner selected the proposed CSV inventory-import service using Python, FastAPI,
SQLite, pytest and Docker, then requested scalable and reusable implementation.
Proceed through build/recovery/concurrency qualification and a second job handler;
record measured limits rather than asserting general large-system readiness.
