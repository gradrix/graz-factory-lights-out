"""One local SQLite authority for prepared Work atoms.

All methods belong to the trusted control plane. A lease fences stale calls; it
is not an authentication boundary. Workers must never receive this DB or API.
No model, filesystem artifact, Git, or container I/O runs inside transactions.
"""

from __future__ import annotations

import json
import math
import sqlite3
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from types import TracebackType
from typing import Any, Self

from pydantic import TypeAdapter

from gflo.artifacts import ArtifactAudit, ArtifactStore
from gflo.records import (
    Acceptance,
    AcceptanceFinding,
    Digest,
    GateEvidence,
    Lease,
    RetryPlan,
    WorkAtom,
)
from gflo.storage import require_space


class Conflict(ValueError):
    """The requested transition no longer applies to the durable state."""


_SCHEMA = (
    """CREATE TABLE atoms (
        atom_id TEXT PRIMARY KEY, idempotency_key TEXT NOT NULL UNIQUE,
        contract TEXT NOT NULL, contract_digest TEXT NOT NULL, created_at REAL NOT NULL
    )""",
    """CREATE TABLE attempts (
        attempt_id TEXT PRIMARY KEY, atom_id TEXT NOT NULL REFERENCES atoms(atom_id),
        ordinal INTEGER NOT NULL CHECK(ordinal > 0), lease TEXT NOT NULL,
        expires_at REAL NOT NULL, strategy TEXT NOT NULL, retry_plan TEXT,
        created_at REAL NOT NULL, UNIQUE(atom_id, ordinal)
    )""",
    """CREATE TABLE state (
        atom_id TEXT PRIMARY KEY REFERENCES atoms(atom_id),
        status TEXT NOT NULL CHECK(status IN
            ('ready','leased','running','validating','retry-ready','quarantined','accepted')),
        active_attempt TEXT REFERENCES attempts(attempt_id), candidate_digest TEXT
    )""",
    """CREATE TABLE events (
        event_id INTEGER PRIMARY KEY, attempt_id TEXT NOT NULL REFERENCES attempts(attempt_id),
        kind TEXT NOT NULL, details TEXT NOT NULL, recorded_at REAL NOT NULL
    )""",
    "CREATE INDEX events_by_attempt ON events(attempt_id, event_id)",
    """CREATE TABLE gates (
        attempt_id TEXT NOT NULL REFERENCES attempts(attempt_id), gate_id TEXT NOT NULL,
        receipt TEXT NOT NULL, PRIMARY KEY(attempt_id, gate_id)
    )""",
    """CREATE TABLE acceptances (
        atom_id TEXT PRIMARY KEY REFERENCES atoms(atom_id),
        attempt_id TEXT NOT NULL UNIQUE REFERENCES attempts(attempt_id), receipt TEXT NOT NULL
    )""",
)


class WorkLedger:
    def __init__(
        self, path: str | Path, *, clock: Callable[[], float] = time.time, reserve_bytes: int = 0
    ):
        self._clock = clock
        self.storage_path = Path(path).parent
        require_space(self.storage_path, reserve_bytes)
        self.artifacts = ArtifactStore(Path(str(path) + ".artifacts"), reserve_bytes=reserve_bytes)
        self._db = sqlite3.connect(path, isolation_level=None, timeout=10)
        self._db.row_factory = sqlite3.Row
        try:
            self._db.execute("PRAGMA foreign_keys=ON")
            if self._db.execute("PRAGMA journal_mode=WAL").fetchone()[0] != "wal":
                raise ValueError("Ledger requires an on-disk WAL database")
            self._db.execute("PRAGMA synchronous=FULL")
            with self._transaction():
                version = self._db.execute("PRAGMA user_version").fetchone()[0]
                if version == 0:
                    if self._db.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchone():
                        raise ValueError("Refusing to initialize an unrecognized database")
                    for statement in _SCHEMA:
                        self._db.execute(statement)
                    for table in ("atoms", "attempts", "events", "gates", "acceptances"):
                        for action in ("UPDATE", "DELETE"):
                            self._db.execute(
                                f"CREATE TRIGGER immutable_{table}_{action} BEFORE {action} "
                                f"ON {table} BEGIN SELECT RAISE(ABORT, 'immutable history'); END"
                            )
                    self._db.execute("PRAGMA user_version=1")
                elif version not in (1, 2, 3):
                    raise ValueError(f"Unsupported ledger schema version: {version}")
                if version < 2:
                    self._db.execute(
                        "CREATE TABLE run_plans (atom_id TEXT PRIMARY KEY "
                        "REFERENCES atoms(atom_id), digest TEXT NOT NULL)"
                    )
                    for action in ("UPDATE", "DELETE"):
                        self._db.execute(
                            f"CREATE TRIGGER immutable_run_plans_{action} BEFORE {action} "
                            "ON run_plans BEGIN SELECT RAISE(ABORT, 'immutable history'); END"
                        )
                    self._db.execute("PRAGMA user_version=2")
        except BaseException:
            self._db.close()
            raise

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self._db.close()

    @contextmanager
    def _transaction(self, *, write: bool = True) -> Iterator[None]:
        self._db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        try:
            yield
            self._db.execute("COMMIT")
        except BaseException:
            # SQLITE_FULL can roll back automatically; preserve the original failure.
            if self._db.in_transaction:
                self._db.execute("ROLLBACK")
            raise

    def check_storage(self) -> None:
        """Admission outside transactions, on both database and artifact filesystems."""
        require_space(self.storage_path, self.artifacts.reserve_bytes)
        require_space(self.artifacts.root, self.artifacts.reserve_bytes)

    def _now(self) -> float:
        now = self._clock()
        if not math.isfinite(now) or now <= 0:
            raise ValueError("Clock must return finite positive Unix seconds")
        return now

    def _atom(self, atom_id: str) -> WorkAtom:
        row = self._db.execute("SELECT contract FROM atoms WHERE atom_id=?", (atom_id,)).fetchone()
        if row is None:
            raise KeyError(atom_id)
        return WorkAtom.model_validate_json(row[0])

    def _state(self, atom_id: str) -> sqlite3.Row:
        row = self._db.execute("SELECT * FROM state WHERE atom_id=?", (atom_id,)).fetchone()
        if row is None:
            raise KeyError(atom_id)
        assert isinstance(row, sqlite3.Row)
        return row

    def _event(self, attempt_id: str, kind: str, details: dict[str, Any], now: float) -> int:
        cursor = self._db.execute(
            "INSERT INTO events(attempt_id,kind,details,recorded_at) VALUES (?,?,?,?)",
            (attempt_id, kind, json.dumps(details, sort_keys=True, allow_nan=False), now),
        )
        assert cursor.lastrowid is not None
        return cursor.lastrowid

    def _lease(self, lease: Lease, *, live: bool = True) -> tuple[sqlite3.Row, sqlite3.Row]:
        lease = Lease.model_validate(lease)
        attempt = self._db.execute(
            "SELECT * FROM attempts WHERE attempt_id=?", (lease.attempt_id,)
        ).fetchone()
        if attempt is None or attempt["lease"] != lease.canonical():
            raise Conflict("Unknown or altered lease")
        state = self._state(lease.atom_id)
        if state["active_attempt"] != lease.attempt_id:
            raise Conflict("Superseded lease")
        if live and (
            state["status"] not in ("leased", "running", "validating")
            or attempt["expires_at"] <= self._now()
        ):
            raise Conflict("Lease expired or attempt is terminal")
        return attempt, state

    def submit(self, atom: WorkAtom) -> str:
        """Submit a prepared, dependency-ready atom; exact resubmission is idempotent."""
        atom = WorkAtom.model_validate(atom)
        for digest in (*atom.dependency_artifacts, *atom.upstream_contracts):
            self.artifacts.verify(digest)
        encoded = atom.canonical()
        with self._transaction():
            existing = self._db.execute(
                "SELECT contract FROM atoms WHERE atom_id=? OR idempotency_key=?",
                (atom.atom_id, atom.idempotency_key),
            ).fetchall()
            if existing:
                if len(existing) == 1 and existing[0][0] == encoded:
                    return atom.atom_id
                raise Conflict("Atom ID or idempotency key already binds a different contract")
            self._db.execute(
                "INSERT INTO atoms VALUES (?,?,?,?,?)",
                (atom.atom_id, atom.idempotency_key, encoded, atom.digest(), self._now()),
            )
            self._db.execute("INSERT INTO state VALUES (?,'ready',NULL,NULL)", (atom.atom_id,))
        return atom.atom_id

    def claim(
        self,
        atom_id: str,
        owner: str,
        *,
        lease_seconds: float = 300,
        retry: RetryPlan | None = None,
    ) -> Lease:
        if (
            type(lease_seconds) not in (int, float)
            or not math.isfinite(lease_seconds)
            or not 0 < lease_seconds <= 86400
        ):
            raise ValueError("Lease duration must be in (0, 86400] seconds")
        if retry is not None:
            retry = RetryPlan.model_validate(retry)
            if retry.new_evidence is not None:
                self.artifacts.verify(retry.new_evidence)
        with self._transaction():
            atom = self._atom(atom_id)
            state = self._state(atom_id)
            if state["status"] not in ("ready", "retry-ready"):
                raise Conflict("Atom is not ready; reconcile expired attempts before claiming")
            ordinal = (
                self._db.execute(
                    "SELECT count(*) FROM attempts WHERE atom_id=?", (atom_id,)
                ).fetchone()[0]
                + 1
            )
            if ordinal > atom.max_attempts:
                raise Conflict("Recovery budget exhausted")
            if state["status"] == "retry-ready":
                prior = self._db.execute(
                    "SELECT strategy FROM attempts WHERE attempt_id=?", (state["active_attempt"],)
                ).fetchone()
                failure = self._db.execute(
                    "SELECT event_id FROM events WHERE attempt_id=? "
                    "AND kind IN ('failed','expired') ORDER BY event_id DESC LIMIT 1",
                    (state["active_attempt"],),
                ).fetchone()
                if retry is None or retry.failure_event != failure[0]:
                    raise Conflict("Retry must reference the latest failure event")
                if retry.strategy == prior[0] and retry.new_evidence is None:
                    raise Conflict("Retry requires a different strategy or new evidence")
                # Reusing the same evidence does not make it new on subsequent retries.
                if retry.new_evidence is not None:
                    for row in self._db.execute(
                        "SELECT retry_plan FROM attempts "
                        "WHERE atom_id=? AND retry_plan IS NOT NULL",
                        (atom_id,),
                    ):
                        previous = RetryPlan.model_validate_json(row[0])
                        if (
                            previous.new_evidence == retry.new_evidence
                            and previous.strategy == retry.strategy
                        ):
                            raise Conflict("Retry repeats a prior strategy/evidence pair")
            elif retry is not None:
                raise Conflict("Initial claim cannot carry a retry plan")
            now = self._now()
            lease = Lease(
                atom_id=atom_id,
                attempt_id=uuid.uuid4().hex,
                token=uuid.uuid4().hex,
                owner=owner,
                expires_at=float(now + lease_seconds),
            )
            self._db.execute(
                "INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?)",
                (
                    lease.attempt_id,
                    atom_id,
                    ordinal,
                    lease.canonical(),
                    lease.expires_at,
                    retry.strategy if retry else "initial",
                    retry.canonical() if retry else None,
                    now,
                ),
            )
            self._db.execute(
                "UPDATE state SET status='leased',active_attempt=?,candidate_digest=NULL "
                "WHERE atom_id=?",
                (lease.attempt_id, atom_id),
            )
            self._event(lease.attempt_id, "leased", {"ordinal": ordinal}, now)
            return lease

    def start(self, lease: Lease) -> None:
        with self._transaction():
            _, state = self._lease(lease)
            if state["status"] != "leased":
                raise Conflict("Only a leased attempt can start")
            self._db.execute("UPDATE state SET status='running' WHERE atom_id=?", (lease.atom_id,))
            self._event(lease.attempt_id, "running", {}, self._now())

    def check_lease(self, lease: Lease) -> None:
        """Fence trusted external work before dispatch; transitions recheck afterward."""
        with self._transaction(write=False):
            self._lease(lease)

    def active_lease(self, atom_id: str) -> Lease:
        """Trusted recovery only; never expose Lease tokens through worker/status APIs."""
        with self._transaction(write=False):
            state = self._state(atom_id)
            row = self._db.execute(
                "SELECT lease FROM attempts WHERE attempt_id=?", (state["active_attempt"],)
            ).fetchone()
            if row is None:
                raise Conflict("No active attempt")
            return Lease.model_validate_json(row[0])

    def bind_run(self, atom_id: str, digest: str) -> None:
        self.artifacts.verify(digest)
        with self._transaction():
            self._atom(atom_id)
            row = self._db.execute(
                "SELECT digest FROM run_plans WHERE atom_id=?", (atom_id,)
            ).fetchone()
            if row is not None:
                if row[0] != digest:
                    raise Conflict("Run plan is immutable")
                return
            self._db.execute("INSERT INTO run_plans VALUES (?,?)", (atom_id, digest))

    def run_plan(self, atom_id: str) -> bytes:
        row = self._db.execute(
            "SELECT digest FROM run_plans WHERE atom_id=?", (atom_id,)
        ).fetchone()
        if row is None:
            raise Conflict("No prepared run is bound to this atom")
        return self.artifacts.read(row[0])

    def observe(self, lease: Lease, kind: str, digest: str) -> None:
        if kind not in ("model", "diagnostic", "candidate-execution"):
            raise ValueError("Unsupported observation kind")
        self.artifacts.verify(digest)
        with self._transaction():
            self._lease(lease)
            self._event(
                lease.attempt_id, "observation", {"kind": kind, "digest": digest}, self._now()
            )

    def candidate(self, lease: Lease, candidate_digest: str) -> None:
        candidate_digest = TypeAdapter(Digest).validate_python(candidate_digest, strict=True)
        self.artifacts.verify(candidate_digest)
        with self._transaction():
            _, state = self._lease(lease)
            if state["status"] != "running":
                raise Conflict("Only a running attempt can submit a candidate")
            self._db.execute(
                "UPDATE state SET status='validating',candidate_digest=? WHERE atom_id=?",
                (candidate_digest, lease.atom_id),
            )
            self._event(lease.attempt_id, "candidate", {"digest": candidate_digest}, self._now())

    def record_gate(self, lease: Lease, evidence: GateEvidence) -> None:
        """Persist a trusted runner receipt. This API must not be exposed to workers."""
        evidence = GateEvidence.model_validate(evidence)
        self.artifacts.verify(evidence.evidence_digest)
        with self._transaction():
            _, state = self._lease(lease)
            atom = self._atom(lease.atom_id)
            spec = next((g for g in atom.required_gates if g.gate_id == evidence.gate_id), None)
            if (
                state["status"] != "validating"
                or spec is None
                or (
                    evidence.attempt_id != lease.attempt_id
                    or evidence.contract_digest != atom.digest()
                    or evidence.inputs_digest != atom.inputs_digest
                    or evidence.candidate_digest != state["candidate_digest"]
                    or evidence.validator_digest != spec.validator_digest
                )
            ):
                raise Conflict("Gate receipt does not bind this contract, attempt and candidate")
            prior = self._db.execute(
                "SELECT receipt FROM gates WHERE attempt_id=? AND gate_id=?",
                (lease.attempt_id, evidence.gate_id),
            ).fetchone()
            if prior is not None:
                if prior[0] == evidence.canonical():
                    return
                raise Conflict("Gate evidence is immutable; revalidation requires a new attempt")
            self._db.execute(
                "INSERT INTO gates VALUES (?,?,?)",
                (lease.attempt_id, evidence.gate_id, evidence.canonical()),
            )
            self._event(
                lease.attempt_id, "gate", {"receipt_digest": evidence.digest()}, self._now()
            )

    def record_finding(self, finding: AcceptanceFinding) -> int:
        """Append contradictory evidence and block reuse without rewriting acceptance.

        Trusted control plane only. Finding evidence must already be published.
        This does not revoke artifacts already exported outside this ledger.
        """
        finding = AcceptanceFinding.model_validate(finding)
        self.artifacts.verify(finding.evidence_digest)
        with self._transaction():
            state = self._state(finding.atom_id)
            atom = self._atom(finding.atom_id)
            if (
                state["status"] != "accepted"
                or state["candidate_digest"] != finding.candidate_digest
                or atom.digest() != finding.contract_digest
            ):
                raise Conflict("Finding does not bind the accepted atom and candidate")
            for row in self._db.execute(
                "SELECT event_id,details FROM events WHERE attempt_id=? "
                "AND kind='acceptance-finding'",
                (state["active_attempt"],),
            ):
                if AcceptanceFinding.model_validate_json(row["details"]) == finding:
                    return int(row["event_id"])
            # Version-2 controllers must not ignore later contradictory evidence.
            self._db.execute("PRAGMA user_version=3")
            return self._event(
                state["active_attempt"],
                "acceptance-finding",
                finding.model_dump(mode="json"),
                self._now(),
            )

    def accept(self, lease: Lease, *, current_inputs_digest: str) -> Acceptance:
        """CAS acceptance using controller-observed preconditions and durable receipts.

        The caller owns the input snapshot while validating/accepting. This method
        cannot detect changes to an external working tree. Artifact bytes are
        reverified before entering the transaction; the append-only store must
        remain exclusively controller-owned, with no concurrent deletion/repair.
        """
        snapshot = self.status(lease.atom_id)
        for digest in (
            snapshot["contract"]["dependency_artifacts"]
            + snapshot["contract"]["upstream_contracts"]
        ):
            self.artifacts.verify(digest)
        # Gates and the candidate are immutable for this attempt. Recheck the
        # lease and all bindings in the transaction after filesystem I/O.
        if snapshot["candidate_digest"] is not None:
            self.artifacts.verify(snapshot["candidate_digest"])
        for attempt in snapshot["attempts"]:
            if attempt["attempt_id"] == lease.attempt_id:
                for receipt in attempt["gate_receipts"]:
                    self.artifacts.verify(receipt["evidence_digest"])
        with self._transaction():
            _, state = self._lease(lease, live=False)
            atom = self._atom(lease.atom_id)
            if current_inputs_digest != atom.inputs_digest:
                raise Conflict("Current preconditions differ from the submitted contract")
            if (
                self._db.execute(
                    "SELECT 1 FROM events WHERE attempt_id=? AND kind='acceptance-finding' LIMIT 1",
                    (state["active_attempt"],),
                ).fetchone()
                is not None
            ):
                raise Conflict(
                    "Accepted result has contradictory evidence; prepare new repair work"
                )
            if state["status"] == "accepted":
                row = self._db.execute(
                    "SELECT receipt FROM acceptances WHERE atom_id=?", (lease.atom_id,)
                ).fetchone()
                return Acceptance.model_validate_json(row[0])
            self._lease(lease)
            if state["status"] != "validating":
                raise Conflict("Attempt has no candidate to accept")
            receipts = [
                GateEvidence.model_validate_json(row[0])
                for row in self._db.execute(
                    "SELECT receipt FROM gates WHERE attempt_id=? ORDER BY gate_id",
                    (lease.attempt_id,),
                )
            ]
            if {r.gate_id for r in receipts} != {g.gate_id for g in atom.required_gates} or any(
                r.outcome != "pass" for r in receipts
            ):
                raise Conflict("Every required gate needs a passing trusted receipt")
            accepted = Acceptance(
                atom_id=atom.atom_id,
                attempt_id=lease.attempt_id,
                contract_digest=atom.digest(),
                inputs_digest=atom.inputs_digest,
                candidate_digest=state["candidate_digest"],
                gate_receipts=tuple(r.digest() for r in receipts),
            )
            self._db.execute(
                "INSERT INTO acceptances VALUES (?,?,?)",
                (atom.atom_id, lease.attempt_id, accepted.canonical()),
            )
            self._db.execute("UPDATE state SET status='accepted' WHERE atom_id=?", (atom.atom_id,))
            self._event(
                lease.attempt_id, "accepted", {"receipt": accepted.model_dump()}, self._now()
            )
            return accepted

    def _finish_failure(self, attempt: sqlite3.Row, kind: str, reason: str, now: float) -> int:
        atom = self._atom(attempt["atom_id"])
        state = "quarantined" if attempt["ordinal"] >= atom.max_attempts else "retry-ready"
        self._db.execute("UPDATE state SET status=? WHERE atom_id=?", (state, atom.atom_id))
        return self._event(attempt["attempt_id"], kind, {"reason": reason, "state": state}, now)

    def fail(self, lease: Lease, reason: str) -> int:
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("Failure requires a diagnostic reason")
        with self._transaction():
            attempt, _ = self._lease(lease)
            return self._finish_failure(attempt, "failed", reason, self._now())

    def reconcile(self) -> list[str]:
        """Fence expired attempts; preserve history and require evidence-derived retries.

        This does not kill old workers or infer that their side effects did not occur.
        The broker must isolate/reconcile their environments before dispatching retries.
        """
        with self._transaction():
            now = self._now()
            expired = self._db.execute(
                "SELECT a.* FROM attempts a JOIN state s ON s.active_attempt=a.attempt_id "
                "WHERE s.status IN ('leased','running','validating') AND a.expires_at<=?",
                (now,),
            ).fetchall()
            for attempt in expired:
                self._finish_failure(
                    attempt, "expired", "Lease expired; side effects require reconciliation", now
                )
            return [str(a["atom_id"]) for a in expired]

    def status(self, atom_id: str) -> dict[str, Any]:
        """Consistent durable snapshot with immutable history; lease tokens are omitted."""
        with self._transaction(write=False):
            atom = self._atom(atom_id)
            state = dict(self._state(atom_id))
            history = []
            for attempt in self._db.execute(
                "SELECT * FROM attempts WHERE atom_id=? ORDER BY ordinal", (atom_id,)
            ):
                events = [
                    dict(row)
                    for row in self._db.execute(
                        "SELECT * FROM events WHERE attempt_id=? ORDER BY event_id",
                        (attempt["attempt_id"],),
                    )
                ]
                for event in events:
                    event["details"] = json.loads(event["details"])
                history.append(
                    {
                        "attempt_id": attempt["attempt_id"],
                        "ordinal": attempt["ordinal"],
                        "owner": Lease.model_validate_json(attempt["lease"]).owner,
                        "expires_at": attempt["expires_at"],
                        "strategy": attempt["strategy"],
                        "retry_plan": json.loads(attempt["retry_plan"])
                        if attempt["retry_plan"]
                        else None,
                        "events": events,
                        "gate_receipts": [
                            GateEvidence.model_validate_json(row[0]).model_dump(mode="json")
                            for row in self._db.execute(
                                "SELECT receipt FROM gates WHERE attempt_id=? ORDER BY gate_id",
                                (attempt["attempt_id"],),
                            )
                        ],
                    }
                )
            findings = [
                event["details"]
                for attempt in history
                for event in attempt["events"]
                if event["kind"] == "acceptance-finding"
            ]
            return {
                **state,
                "contract": atom.model_dump(mode="json"),
                "attempts": history,
                "acceptance_findings": findings,
                "acceptance_challenged": bool(findings),
            }

    def audit_artifacts(self) -> ArtifactAudit:
        """Inspect all stored byte references, including failed/superseded attempts.

        Contract/input/schema/validator identities and receipt hashes identify
        external inputs or SQLite records, not byte objects in this store.
        No collection is performed, including for publication-before-commit orphans.
        """
        references: set[str] = set()
        with self._transaction(write=False):
            for row in self._db.execute("SELECT digest FROM run_plans"):
                references.add(row[0])
            for row in self._db.execute("SELECT details FROM events WHERE kind='observation'"):
                references.add(json.loads(row[0])["digest"])
            for row in self._db.execute(
                "SELECT details FROM events WHERE kind='acceptance-finding'"
            ):
                finding = AcceptanceFinding.model_validate_json(row[0])
                references.update((finding.candidate_digest, finding.evidence_digest))
            for row in self._db.execute("SELECT contract FROM atoms"):
                atom = WorkAtom.model_validate_json(row[0])
                references.update((*atom.dependency_artifacts, *atom.upstream_contracts))
            for row in self._db.execute("SELECT details FROM events WHERE kind='candidate'"):
                references.add(json.loads(row[0])["digest"])
            for row in self._db.execute("SELECT receipt FROM gates"):
                references.add(GateEvidence.model_validate_json(row[0]).evidence_digest)
            for row in self._db.execute(
                "SELECT retry_plan FROM attempts WHERE retry_plan IS NOT NULL"
            ):
                evidence = RetryPlan.model_validate_json(row[0]).new_evidence
                if evidence is not None:
                    references.add(evidence)
        return self.artifacts.audit(references)
