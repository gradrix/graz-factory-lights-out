"""Local control-plane CLI; deliberately has no worker-facing acceptance command."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from gflo.broker import BrokerError, DockerBroker
from gflo.controller import Controller, RunPlan, prepare_run
from gflo.history import change_history, render_history
from gflo.integration import IntegrationPlan, IntegrationState, integrate
from gflo.ledger import Conflict, WorkLedger
from gflo.model import LocalModel, ModelError
from gflo.records import WorkAtom
from gflo.reporting import cost_report


def main() -> int:
    parser = argparse.ArgumentParser(description="GFLO durable prepared-task ledger")
    parser.add_argument("--db", type=Path, default=Path(".gflo/ledger.sqlite3"))
    parser.add_argument(
        "--reserve-bytes",
        type=int,
        default=0,
        help="Minimum free control-plane storage; 0 disables admission (development default)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    submit = commands.add_parser("submit", help="Validate and durably submit a prepared atom JSON")
    submit.add_argument("contract", type=Path)
    status = commands.add_parser("status", help="Show state and attempt history")
    status.add_argument("atom_id")
    report = commands.add_parser("report", help="Report cumulative model costs including retries")
    report.add_argument("atom_id")
    history = commands.add_parser("history", help="Review retained candidate diffs and outcomes")
    history.add_argument("atom_id")
    history.add_argument("--format", choices=("text", "json"), default="text")
    resume = commands.add_parser("resume", help="Resume a prepared run, or reconcile leases only")
    resume.add_argument("atom_id", nargs="?")
    run = commands.add_parser("run", help="Execute a previously submitted prepared run")
    run.add_argument("atom_id")
    integration = commands.add_parser("integrate", help="Validate a prepared combined candidate")
    integration.add_argument("plan", type=Path)
    integration.add_argument("--current-state", type=Path, required=True)
    prepared = commands.add_parser("submit-run", help="Validate and persist a complete run plan")
    prepared.add_argument("plan", type=Path)
    commands.add_parser("audit-artifacts", help="Verify stored references; never delete content")
    args = parser.parse_args()
    try:
        # Reject malformed submissions before opening or creating the ledger.
        atom = (
            WorkAtom.model_validate_json(args.contract.read_bytes())
            if args.command == "submit"
            else None
        )
        plan = (
            RunPlan.model_validate_json(args.plan.read_bytes())
            if args.command == "submit-run"
            else None
        )
        if atom is not None or plan is not None:
            args.db.parent.mkdir(parents=True, exist_ok=True)
        elif not args.db.is_file():
            raise ValueError("Ledger does not exist; submit a prepared atom first")
        with WorkLedger(args.db, reserve_bytes=args.reserve_bytes) as ledger:
            output: dict[str, Any]
            if atom is not None:
                output = {"atom_id": ledger.submit(atom)}
            elif plan is not None:
                output = {"atom_id": prepare_run(ledger, plan)}
            elif args.command == "integrate":
                integration_plan = IntegrationPlan.model_validate_json(args.plan.read_bytes())
                output = integrate(
                    ledger,
                    integration_plan,
                    DockerBroker(ledger.artifacts, integration_plan.broker_image),
                    lambda: IntegrationState.model_validate_json(args.current_state.read_bytes()),
                )
                print(json.dumps(output, indent=2))
                return 0 if output["status"] == "accepted" else 2
            elif args.command == "status":
                output = ledger.status(args.atom_id)
            elif args.command == "report":
                output = cost_report(ledger, args.atom_id)
            elif args.command == "history":
                output = change_history(ledger, args.atom_id)
                if args.format == "text":
                    print(render_history(output), end="")
                    return 0
            elif args.command == "audit-artifacts":
                output = asdict(ledger.audit_artifacts())
            elif args.command == "run" or (args.command == "resume" and args.atom_id):
                saved = RunPlan.model_validate_json(ledger.run_plan(args.atom_id))
                controller = Controller(
                    ledger,
                    LocalModel(ledger.artifacts, saved.model_profile),
                    DockerBroker(ledger.artifacts, saved.broker_image),
                )
                output = controller.run(args.atom_id)
                print(json.dumps(output, indent=2))
                return 0 if output["status"] == "accepted" else 2
            else:
                output = {"reconciled_atoms": ledger.reconcile(), "workers_dispatched": False}
        print(json.dumps(output, indent=2))
        return 0
    except ValidationError as exc:
        print(
            json.dumps(
                {
                    "error": "Invalid work contract",
                    "details": exc.errors(
                        include_url=False, include_context=False, include_input=False
                    ),
                }
            ),
            file=sys.stderr,
        )
    except (
        OSError,
        sqlite3.Error,
        Conflict,
        ValueError,
        KeyError,
        ModelError,
        BrokerError,
        subprocess.SubprocessError,
    ) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
    except KeyboardInterrupt:
        print(
            json.dumps({"error": "Interrupted; resume the prepared atom to reconcile work"}),
            file=sys.stderr,
        )
        return 130
    return 1
