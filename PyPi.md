# PyPi cheatsheet

## Generation and upload to testing PyPi
```bash
	git tag 0.1.0
	python3 setup.py sdist
	python3 -m twine upload --repository testpypi dist/*
```

## Testing installation

Since TestPyPI doesn’t have the same packages as the live PyPI, it’s possible that attempting to install dependencies may fail or install something unexpected. It is a good practice to avoid installing dependencies when using TestPyPI.

```bash
	python3 -m pip install --no-deps --index-url https://test.pypi.org/simple/ tessw-publisher
```

## Generation and Upload to PyPi

```bash
	git tag 0.1.0
	python3 setup.py sdist
	python3 -m twine upload --repository testpypi dist/*
```

