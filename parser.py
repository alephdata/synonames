import sys
import json
import click
import logging
from rdflib import Graph, Namespace
from rdflib.namespace import SKOS, RDFS

SCHEMA = Namespace("http://schema.org/")
PROP = Namespace("http://www.wikidata.org/prop/direct/")

ENTITY = Namespace('http://www.wikidata.org/entity/')
SPECIAL = 'https://www.wikidata.org/wiki/Special:EntityData/'


def parse_triples(fh, size=1000):
    line_no = 0
    while True:
        line = fh.readline()
        line_no += 1
        if not line:
            break
        if line_no % 1000 == 0:
            print("LINE", line_no)
        try:
            graph = Graph()
            graph.parse(data=line, format='nt')
            yield from graph
        except Exception:
            pass


@click.command()
@click.option('-i', '--input', type=click.File('r'), default='-')  # noqa
@click.option('-o', '--output', type=click.File('w'), default='-')  # noqa
def transform(input, output):
    prev = None
    names = []
    person = False
    for (s, p, o) in parse_triples(input):
        if s != prev and prev is not None:
            if person and len(set(names)) > 1:
                output.write(json.dumps(names))
                output.write('\n')
                output.flush()
            names = []
            person = False
        prev = s
        if p in [PROP.P31]:
            if o == ENTITY['Q5']:
                person = True
        if p in [SCHEMA.name, RDFS.label, SKOS.prefLabel, SKOS.altLabel]:
            names.append(str(o))


if __name__ == '__main__':
    transform()
