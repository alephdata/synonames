
parse:
	curl -s https://dumps.wikimedia.org/wikidatawiki/entities/latest-truthy.nt.bz2 | bzcat | python3 parser.py

build:
	docker built -t alephdata/synonames .