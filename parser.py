import os
import click
import dataset
from rdflib import Graph, Namespace
from rdflib.namespace import SKOS, RDFS
from dataset.chunked import ChunkedInsert

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
        # if line_no % 1000 == 0:
        #     print("LINE", line_no)
        try:
            graph = Graph()
            graph.parse(data=line, format='nt')
            yield from graph
        except Exception:
            pass


@click.command()
@click.option('-i', '--input', type=click.File('r'), default='-')  # noqa
def transform(input):
    db_uri = os.environ.get('DATABASE_URI')
    engine = dataset.connect(db_uri)
    table = engine.get_table('names')
    bulk = ChunkedInsert(table, chunksize=10000)
    prev = None
    languages = {}
    person = False
    for (s, p, o) in parse_triples(input):
        if s != prev and prev is not None:
            if person and len(set(languages)) > 1:
                print(prev)
                for lang, names in languages.items():
                    for name in names:
                        bulk.insert({
                            'uri': prev,
                            'lang': lang,
                            'name': name
                        })
            languages = {}
            person = False
        prev = s
        if p in [PROP.P31]:
            if o == ENTITY['Q5']:
                person = True
        if p in [SCHEMA.name, RDFS.label, SKOS.prefLabel, SKOS.altLabel]:
            if o.language not in languages:
                languages[o.language] = []
            name = str(o)
            if name not in languages[o.language]:
                languages[o.language].append(name)
    bulk.flush()


if __name__ == '__main__':
    transform()
