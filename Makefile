.PHONY: test coverage doctor

test:
	python3 -m unittest discover -s tests -v

coverage:
	.venv/bin/coverage erase
	.venv/bin/coverage run -m unittest discover -s tests -v
	.venv/bin/coverage combine
	.venv/bin/coverage report

doctor:
	python3 -m gflo doctor
