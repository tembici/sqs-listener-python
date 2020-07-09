SRC = sqs_listener tests setup.py

## help            -> Show help
help: Makefile
	@sed -nr 's/^## ?//p' $^

## test            -> Run all tests in the project
test:
	python -m unittest discover tests

check: coverage flake8-check black-check isort-check mypy-check

## coverage        -> Run all tests in the project and show coverage. It'll fail if coverage < 100
coverage:
	coverage run --source='.' --omit='venv/*' -m unittest discover tests && coverage report

## flake8-check    -> Check flake8
flake8-check:
	@if ! flake8 $(SRC); then \
            flake8 --count $(SRC); \
            false; \
	fi

## black-check     -> Check black code style
black-check:
	@if ! black --check $(SRC); then \
            black --diff $(SRC); \
            false; \
	fi

## isort-check     -> Check project imports structure
isort-check:
	@if ! isort -rc --check-only $(SRC); then \
            isort --diff -rc $(SRC); \
            false; \
	fi

## mypy-check      -> Check project type hints
mypy-check:
	python -m mypy_boto3 && mypy .

.PHONY: help test coverage isort-check black-check flake8-check check mypy-check
