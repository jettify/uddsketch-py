# Some simple testing tasks (sorry, UNIX only).

FILES := uddsketch tests examples setup.py



flake:
	flake8  ${FILES}

test:
	pytest -sv

vtest:
	pytest -sv -vv

checkrst:
	python setup.py check --restructuredtext

pyroma:
	pyroma -d .

bandit:
	bandit -r ./uddsketch

mypy:
	mypy uddsketch --ignore-missing-imports

checkbuild:
	python setup.py sdist bdist_wheel
	twine check dist/*

cov cover coverage:
	pytest -sv -vv --cov=uddsketch --cov-report=xml --cov-report=term --cov-report=html ./tests
	@echo "open file://`pwd`/htmlcov/index.html"

checkfmt:
	isort --check-only --diff $(FILES)
	black -l 79 --check $(FILES)

lint: flake checkrst pyroma bandit checkfmt

clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -f `find . -type f -name '@*' `
	rm -f `find . -type f -name '#*#' `
	rm -f `find . -type f -name '*.orig' `
	rm -f `find . -type f -name '*.rej' `
	rm -f .coverage
	rm -rf coverage
	rm -rf build
	rm -rf cover
	rm -rf dist
	rm -rf docs/_build

doc:
	make -C docs html
	@echo "open file://`pwd`/docs/_build/html/index.html"

black:
	black -l 79 $(FILES)

fmt:
	isort ${FILES}
	black -l 79 ${FILES}

ci: lint cov checkbuild

.PHONY: all flake test vtest cov clean doc
