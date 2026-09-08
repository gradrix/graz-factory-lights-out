"""Print a complete prepared slug task without contacting Docker or a model."""

import argparse
from pathlib import Path

from gflo.pilot import fixtures, make_plan


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path,
        default=root / "infra/serving/vllm-5090-graphs.example.json",
    )
    args = parser.parse_args()
    plan = make_plan(
        fixtures()[0], args.config.read_text(), root / "examples/work-atom.json"
    )
    print(plan.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
