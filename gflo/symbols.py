"""Derived, bounded Python definitions; source identity remains authoritative."""

from __future__ import annotations

import ast
import sys
from typing import Annotated, Literal

from pydantic import Field

from gflo.artifacts import ArtifactStore
from gflo.records import Digest, Record
from gflo.repository import Repository, RepositoryError, SourceRead, SourceRef, _within

ANALYZER = f"python-definitions-v1:{sys.version_info.major}.{sys.version_info.minor}"
MAX_PARSE_BYTES = 512 * 1024


class Definition(Record):
    name: str
    qualified_name: str
    kind: Literal["class", "function", "async-function"]
    line: Annotated[int, Field(ge=1)]
    end_line: Annotated[int, Field(ge=1)]


class FileSymbols(Record):
    analyzer: str
    file_digest: Digest
    definitions: Annotated[tuple[Definition, ...], Field(max_length=1000)]


class SymbolIndex(Record):
    kind: Literal["python-symbol-index-v1"] = "python-symbol-index-v1"
    source: SourceRef
    analyzer: str
    scopes: tuple[str, ...]
    files: dict[str, Digest]
    skipped: dict[str, str]
    eligible_files: int
    non_python_files: int


class SymbolBuild(Record):
    index_digest: Digest
    parsed_files: int
    reused_files: int
    skipped_files: int


class SymbolHit(Record):
    source: SourceRef
    index_digest: Digest
    path: str
    file_digest: Digest
    definition: Definition


class SymbolResult(Record):
    source: SourceRef
    index_digest: Digest
    analyzer: str
    scopes: tuple[str, ...]
    hits: tuple[SymbolHit, ...]
    complete: bool
    indexed_files: int
    eligible_files: int
    skipped: dict[str, str]
    truncated: bool
    meaning: Literal["Python definitions only; no caller or dynamic-binding analysis"] = (
        "Python definitions only; no caller or dynamic-binding analysis"
    )


def _analyze(data: bytes, digest: str) -> FileSymbols:
    tree = ast.parse(data.decode("utf-8"))
    definitions = []
    pending: list[tuple[ast.AST, tuple[str, ...]]] = [(tree, ())]
    visited = name_bytes = 0
    while pending:
        node, parents = pending.pop()
        visited += 1
        if visited > 50000:
            raise ValueError("node-budget")
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            qualified = (*parents, node.name)
            name_bytes += len(".".join(qualified).encode())
            if name_bytes > 262144:
                raise ValueError("name-budget")
            definitions.append(
                Definition(
                    name=node.name,
                    qualified_name=".".join(qualified),
                    kind="class"
                    if isinstance(node, ast.ClassDef)
                    else "async-function"
                    if isinstance(node, ast.AsyncFunctionDef)
                    else "function",
                    line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                )
            )
            if len(definitions) > 1000:
                raise ValueError("symbol-budget")
            parents = qualified
        pending.extend((child, parents) for child in reversed(list(ast.iter_child_nodes(node))))
    return FileSymbols(analyzer=ANALYZER, file_digest=digest, definitions=tuple(definitions))


def build_symbols(
    repository: Repository,
    artifacts: ArtifactStore,
    *,
    prior_digest: str | None = None,
    max_files: int = 1000,
    max_bytes: int = 8 * 1024 * 1024,
) -> SymbolBuild:
    """Publish bounded analysis and coverage, reusing only exact-content analyzer matches."""
    if not 1 <= max_files <= 10000 or not 1 <= max_bytes <= 16 * 1024 * 1024:
        raise RepositoryError("Invalid symbol indexing budget")
    prior = SymbolIndex.model_validate_json(artifacts.read(prior_digest)) if prior_digest else None
    paths = sorted(p for p in repository.source.files if _within(p, repository.scopes))
    eligible = [p for p in paths if p.endswith(".py")]
    files: dict[str, str] = {}
    skipped = {}
    consumed = parsed = reused = admitted = 0
    for path in eligible:
        entry = repository.source.files[path]
        if admitted >= max_files:
            skipped[path] = "file-budget"
            continue
        if entry.size_bytes > MAX_PARSE_BYTES:
            skipped[path] = "parse-byte-budget"
            continue
        if consumed + entry.size_bytes > max_bytes:
            skipped[path] = "byte-budget"
            continue
        admitted += 1
        consumed += entry.size_bytes
        if prior is not None and prior.analyzer == ANALYZER and path in prior.files:
            digest = prior.files[path]
            shard = FileSymbols.model_validate_json(artifacts.read(digest))
            if shard.analyzer == ANALYZER and shard.file_digest == entry.content_digest:
                files[path] = digest
                reused += 1
                continue
        data = repository._bytes(path)
        try:
            shard = _analyze(data, entry.content_digest)
        except (SyntaxError, UnicodeError):
            skipped[path] = "parse-error"
            continue
        except (RecursionError, ValueError):
            skipped[path] = "analysis-budget"
            continue
        files[path] = artifacts.publish(shard.canonical().encode())
        parsed += 1
    index = SymbolIndex(
        source=repository.source.ref,
        analyzer=ANALYZER,
        scopes=repository.scopes,
        files=files,
        skipped=skipped,
        eligible_files=len(eligible),
        non_python_files=len(paths) - len(eligible),
    )
    return SymbolBuild(
        index_digest=artifacts.publish(index.canonical().encode()),
        parsed_files=parsed,
        reused_files=reused,
        skipped_files=len(skipped),
    )


def query_symbols(
    repository: Repository,
    artifacts: ArtifactStore,
    index_digest: str,
    query: str,
    *,
    max_hits: int = 100,
) -> SymbolResult:
    """Exact simple/qualified definition names, with explicit partial-result coverage."""
    if not query or len(query) > 200 or not 1 <= max_hits <= 1000:
        raise RepositoryError("Invalid symbol query or hit budget")
    index = SymbolIndex.model_validate_json(artifacts.read(index_digest))
    if index.source != repository.source.ref or index.analyzer != ANALYZER:
        raise RepositoryError("Symbol index belongs to another source or analyzer")
    if index.scopes != repository.scopes:
        raise RepositoryError("Symbol index belongs to another scope")
    eligible = {
        p for p in repository.source.files if p.endswith(".py") and _within(p, repository.scopes)
    }
    if (
        set(index.files) & set(index.skipped)
        or set(index.files) | set(index.skipped) != eligible
        or index.eligible_files != len(eligible)
    ):
        raise RepositoryError("Symbol index coverage differs from source inventory")
    hits: list[SymbolHit] = []
    truncated = False
    for path, digest in sorted(index.files.items()):
        shard = FileSymbols.model_validate_json(artifacts.read(digest))
        if (
            shard.analyzer != ANALYZER
            or shard.file_digest != repository.source.files[path].content_digest
        ):
            raise RepositoryError("Symbol shard differs from source or analyzer")
        for definition in shard.definitions:
            if query not in (definition.name, definition.qualified_name):
                continue
            if len(hits) == max_hits:
                truncated = True
                continue
            hits.append(
                SymbolHit(
                    source=repository.source.ref,
                    index_digest=index_digest,
                    path=path,
                    file_digest=shard.file_digest,
                    definition=definition,
                )
            )
    return SymbolResult(
        source=repository.source.ref,
        index_digest=index_digest,
        analyzer=ANALYZER,
        scopes=repository.scopes,
        hits=tuple(hits),
        complete=not index.skipped and not truncated,
        indexed_files=len(index.files),
        eligible_files=len(eligible),
        skipped=index.skipped,
        truncated=truncated,
    )


def read_symbol(repository: Repository, hit: SymbolHit, *, max_lines: int = 80) -> SourceRead:
    """Resolve a location through authoritative source access; never execute an index."""
    hit = SymbolHit.model_validate(hit)
    if (
        hit.source != repository.source.ref
        or repository._entry(hit.path).content_digest != hit.file_digest
    ):
        raise RepositoryError("Symbol hit belongs to another source")
    return repository.read(
        hit.path,
        start_line=hit.definition.line,
        max_lines=min(max_lines, hit.definition.end_line - hit.definition.line + 1),
    )
