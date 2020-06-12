## help            -> Show help
.PHONY: help
help: Makefile
	@sed -nr 's/^## ?//p' $^

## test            -> Run all tests in the project
.PHONY: test
test:
	python -m unittest discover tests

## coverage        -> Run all tests in the project and show coverage. It'll fail if coverage < 100
.PHONY: coverage
coverage:
	coverage run --source='.' -m unittest discover tests && coverage report --fail-under=100 -m
