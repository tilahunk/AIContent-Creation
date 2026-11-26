PYTHON = python

.PHONY: install validate test film status
install:
	$(PYTHON) -m pip install -r requirements.txt

validate:
	$(PYTHON) -m pipeline.cli validate

test:
	$(PYTHON) -m pytest -q

film:
	$(PYTHON) -m pipeline.cli run

status:
	$(PYTHON) -m pipeline.cli status

