build:
	python setup.py bdist_wheel

clean:
	-rm -rf dist/ build/ classify_bills.egg-info/

