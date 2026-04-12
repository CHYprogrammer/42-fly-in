program = fly_in.py
package = pydantic


install:

run:

lint:
	flake8
	mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --

lint-strict:

clean: