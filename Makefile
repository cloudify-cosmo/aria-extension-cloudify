.PHONY: release install files test docs prepare publish

all:
	@echo "make release - prepares a release and publishes it"
	@echo "make dev - prepares a development environment"
	@echo "make install - install on local system"
	@echo "make files - update changelog and todo files"
	@echo "make test - run tox"
	@echo "make docs - build docs"
	@echo "prepare - prepare module for release (CURRENTLY IRRELEVANT)"
	@echo "make publish - upload to pypi"

release: test docs publish

dev:
	pip install -r dev-requirements.txt
	python setup.py develop

install:
	python setup.py install

test:
	pip install tox==1.6.1
	tox

docs:
	cd docs && make html
	pandoc README.md -f markdown -t rst -s -o README.rst


publish:
	python setup.py sdist upload
