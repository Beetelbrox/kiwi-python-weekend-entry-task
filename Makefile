
format:
	isort flight_search/ test/
	black flight_search/ test/

zip:
	zip -r kiwi-weekend-challenge-fjjm.zip . -x .venv\* .pytest_cache\* **/__pycache__\* ./.git\*