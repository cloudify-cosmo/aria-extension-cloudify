.PHONY: release install files test docs prepare publish

all:
	@echo "make release - prepares a release and publishes it"
	@echo "make dev - prepares a development environment"
	@echo "make install - install on local system"
	@echo "make test - run tox"
	@echo "make docs - build docs"
	@echo "prepare - prepare module for release"
	@echo "make publish - upload to pypi"

release: test docs publish

dev:
	pip install -r dev-requirements.txt
	pip install -e $(shell pwd)

install:
	python setup.py install

test:
	pip install -r tests/requirements.txt
	tox

docs:
	cd docs && make html
	pandoc README.md -f markdown -t rst -s -o README.rst

prepare:
	python setup.py sdist

publish: prepare
	python setup.py upload

cleanup:
	rm -fr dist/ aria.egg-info/ .tox/ .coverage
	find . -name "*.pyc" -exec rm -rf {} \;
