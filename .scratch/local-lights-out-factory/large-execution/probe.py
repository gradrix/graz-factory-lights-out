"""Measure real committed factory build inputs against the existing execution adapter."""

import json
import subprocess
from pathlib import Path

from gflo.artifacts import ArtifactStore
from gflo.broker import SourceBundle
from gflo.repository import (
    FileIdentity,
    Repository,
    RepositoryError,
    Snapshot,
    SnapshotSource,
    SourceRef,
)

HERE = Path(__file__).resolve().parent
ROOT = Path(".gflo/evidence/large-execution-v1")
COMMIT = "3085d46"


def main():
    ROOT.mkdir(parents=True, exist_ok=False)
    artifacts = ArtifactStore(ROOT / "artifacts")
    commit = subprocess.check_output(["git", "rev-parse", COMMIT], text=True).strip()
    paths = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", commit, "gflo", "tests", "pyproject.toml"],
        text=True,
    ).splitlines()
    files = {p: subprocess.check_output(["git", "show", f"{commit}:{p}"]) for p in paths}
    manifest = Snapshot(
        files={
            p: FileIdentity(
                content_digest=artifacts.publish(data), size_bytes=len(data), executable=False
            )
            for p, data in files.items()
        }
    )
    ref = SourceRef(
        kind="repository-snapshot-v1",
        artifact_digest=artifacts.publish(manifest.canonical().encode()),
    )
    repository = Repository(SnapshotSource(artifacts, ref))
    rows = []
    for name, selected in [
        ("runtime", tuple(p for p in paths if p.startswith("gflo/"))),
        ("tests", tuple(p for p in paths if p.startswith("tests/"))),
        ("full-python-build", tuple(paths)),
    ]:
        row = dict(
            name=name, file_count=len(selected), source_bytes=sum(len(files[p]) for p in selected)
        )
        try:
            bundle = SourceBundle(files={p: files[p].decode() for p in selected})
        except ValueError as exc:
            row["bundle_admitted"] = False
            row["bundle_error"] = str(exc).splitlines()[1].strip().split(" [type=", 1)[0]
        else:
            row["bundle_admitted"] = True
            row["canonical_bytes"] = len(bundle.canonical().encode())
        try:
            repository.select(selected, purpose="execution")
        except RepositoryError as exc:
            row["execution_admitted"] = False
            row["execution_error"] = str(exc)
        else:
            row["execution_admitted"] = True
        assert not row["execution_admitted"] and not row["bundle_admitted"]
        rows.append(row)
    context = repository.select(("gflo/artifacts.py",), purpose="context", max_bytes=16000)
    assert context.bundle and "gflo/artifacts.py" in context.bundle.files
    result = dict(
        commit=commit,
        snapshot=ref.model_dump(mode="json"),
        snapshot_files=len(files),
        snapshot_bytes=sum(map(len, files.values())),
        bounded_context_admitted=True,
        execution_limit_bytes=262144,
        execution_limit_files=100,
        workloads=rows,
        conclusion=(
            "Snapshot identity and bounded context work; current SourceBundle "
            "execution cannot admit even all runtime files. No large build was executed."
        ),
    )
    (HERE / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
