# Accept private Python interface names

Type: task
Status: resolved

## Evidence and scope

Both fresh Taskdock repair planners exhausted their budgets because
InterfaceDeclaration.symbol reused the general Identifier constraint, which rejects
leading underscores. `_validate_title` and `_validate_storage` are valid Python
function names present in the source. One planner repeated this valid declaration
through all six responses. This is a controller schema error, not a missing product
decision. Preserve those planning halts and their costs.

Allow private Python names specifically in interface declarations, preserving all
previously valid values and their canonical identities. Keep general identifiers,
source/write scope, declaration-body validation and independent gates unchanged.
Add a red-capable regression, run contract/planning tests and historical replays,
then qualify fresh repair plans against the same requests, gates, model and budgets.

## Answer

Interface declarations now admit leading-underscore names without widening general identifiers. Three red-capable private-symbol regressions, 533 tests/25 subtests with Docker, typing/lint and four unchanged historical replays pass. Two exact retained plans validate unchanged. Fresh v3 planning and accepted repair exercise the fix; v2 preparation mismatch is separately recorded. See [evidence](../small-project/README.md).
