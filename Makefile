
all: run

build: parse generate

generate:
	python src/generate.py

fetch:
	wget -O /data/latest-truthy.nt.bz2 https://dumps.wikimedia.org/wikidatawiki/entities/latest-truthy.nt.bz2

parse:
	curl -s https://dumps.wikimedia.org/wikidatawiki/entities/latest-truthy.nt.bz2 | bzcat | python3 src/parser.py

build:
	docker-compose build

shell:
	docker-compose run --rm worker bash

down:
	docker-compose down