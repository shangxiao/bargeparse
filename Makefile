.PHONY: build clean

build:
	git stash -u
	python -m pep517.build .
	git stash pop

deploy:
	twine upload dist/*

clean:
	rm -rf dist/ build/ bargeparse.egg-info
