format:
	black . -l 79
	linecheck . --fix
test:
	pytest -m 'not local' --cov=./ --cov-report=xml --maxfail=0
