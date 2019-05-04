
fetch:
	wget https://dumps.wikimedia.org/wikidatawiki/entities/latest-truthy.nt.bz2

parse:
	bzcat latest-truthy.nt.bz2 | python parser.py -o names.ijson