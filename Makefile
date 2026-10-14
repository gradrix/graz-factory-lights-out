.PHONY: test check rig-check rig-gate coverage doctor

test:  # host Python: rig/runtime only; use `make check` on the development machine
	python3 -m unittest discover -s tests -v

check:
	ops/check.sh

rig-check:
	ops/rig_check.sh

rig-gate:  # LABEL=name [ARGS="--smoke"]; docs/model-upgrade.md
	ops/rig_gate.sh $(LABEL) $(ARGS)

coverage:
	.venv/bin/coverage erase
	.venv/bin/coverage run -m unittest discover -s tests -v
	.venv/bin/coverage combine
	.venv/bin/coverage report

doctor:
	python3 -m gflo doctor
