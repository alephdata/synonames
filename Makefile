
all: run

build: parse generate

generate:
	python3 generate.py

parse:
	curl -s https://dumps.wikimedia.org/wikidatawiki/entities/latest-truthy.nt.bz2 | bzcat | python3 parser.py

build:
	docker build -t alephdata/synonames .

run: build
	docker-compose run --rm worker bash

down:
	docker-compose down