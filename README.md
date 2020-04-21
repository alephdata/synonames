# Name alias generation

`synonames` generates aliases for human names across cultural environments. Names often
have different spellings in different languages and cultures - for example, Alexander
can also be Alexandr or Oleksandr. This repository reads a data dump from Wikidata to
filter out every human name from every language edition of Wikipedia and map them across
language editions.

The resulting file can be used as a set of synonyms, for example to expand search queries
against a dataset about people.

### Links

* https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-synonym-tokenfilter.html
* https://gist.github.com/dchaplinsky/ad68e3d0887db44766a459c806dbd9d7
