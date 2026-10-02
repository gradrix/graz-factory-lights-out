.PHONY: test coverage doctor

test:
	python3 -m unittest discover -s tests -v

coverage:
	.venv/bin/coverage run --branch --source=gflo -m unittest discover -s tests -v
	.venv/bin/coverage report --fail-under=85 -m

doctor:
	python3 -m gflo doctor
