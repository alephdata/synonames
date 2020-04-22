
all: shell

build: parse generate

generate:
	python3 src/generate.py

pairs:
	python3 src/pairs.py

/data/latest-truthy.nt.bz2:
	wget -O /data/latest-truthy.nt.bz2 https://dumps.wikimedia.org/wikidatawiki/entities/latest-truthy.nt.bz2

parse:
	curl -s https://dumps.wikimedia.org/wikidatawiki/entities/latest-truthy.nt.bz2 | bzcat | python3 src/parser.py

parse-local: /data/latest-truthy.nt.bz2
	bzcat /data/latest-truthy.nt.bz2 | python3 src/parser.py

build:
	docker-compose build

shell:
	docker-compose run --rm worker bash

down:
	docker-compose down