# Issue tracker: Local Markdown

Issues and specs live under `.scratch/<feature-slug>/`.
Keep handoffs, issues, and research in version control so development can resume
on another machine. Include new files when committing the corresponding work.
Public priorities live in `docs/roadmap.md`; detailed continuation starts at
`.scratch/local-lights-out-factory/HANDOFF.md`. Raw runtime evidence belongs in
ignored `.gflo/` and requires a separate transfer when historical runs are needed.

## Conventions

- Specs: `<feature>/spec.md`, relative to `.scratch/`.
- Tickets: `<feature>/issues/<NN>-<slug>.md`, numbered from 01.
  Use one file per ticket and the next unused number.
- Record triage state in a `Status:` line near the top, using
  `docs/agents/triage-labels.md`.
- Wayfinding also uses `Status: claimed` and `Status: resolved`.
  Preserve these states when reading existing tickets.
- Append conversation under `## Comments`.

## Publish and fetch

When publishing a ticket, create its issue file.
When publishing a spec, write its spec file.

When fetching a ticket, read the referenced file. Resolve a bare
number within the relevant feature; ask if it is ambiguous.
Read linked material as needed for the task.

## Wayfinding

- Map: `.scratch/<feature>/map.md`, containing notes,
  decisions so far, and open questions.
- Child tickets use `Type: research`, `prototype`, `grilling`,
  or `task`.
- Dependencies: `Blocked by: NN, NN`. A ticket is unblocked
  when every listed dependency has `Status: resolved`.
- Frontier: choose the first eligible ticket by number:
  unresolved, unblocked, unclaimed, and ready for the actor
  under the applicable skill's triage rules.
- Claim: set `Status: claimed` before beginning work.
- Resolve: append the answer under `## Answer`, set
  `Status: resolved`, and add a gist and link to the map's
  decisions so far.
