# Pin fixed SQLite for concurrent jobs

Type: task
Status: resolved

## Evidence and scope

The Importflow base image links SQLite 3.46.1. SQLite's official WAL documentation
identifies versions through 3.51.2 as affected by the WAL-reset race, fixed in 3.51.3
and later (also selected backports). Our workload uses multiple writing processes.
Build a separately pinned image with fixed upstream SQLite, retain source checksum
and linkage proof, and rerun reference/generation/runtime qualification. Preserve
frozen earlier images and trials without promoting their concurrency results. Do
not mutate host/factory SQLite or reinterpret old image identities.

Source: https://www.sqlite.org/wal.html#walreset

## Answer

Fixed upstream SQLite 3.51.3 is installed through the image system loader.
Broker and child-process probes confirm actual linkage after environment sanitization;
11 reference cases and the larger real-HTTP/four-worker audit pass. Prior LD-path-only
and original images remain identified separately. No host SQLite changed. The fresh
continuation used the admitted image but its parser still failed; no application
qualification is inferred. [Evidence](../importflow/README.md).
