import re
# import json
import click
from Levenshtein import distance
from itertools import combinations
from normality import ascii_text
from dataset.chunked import ChunkedInsert
from common import get_db


def iter_names(engine):
    table = engine.get_table('names')
    entity = None
    names = set()
    for row in table.find(order_by='uri'):
        uri = row.get('uri')
        entity = entity or uri
        if uri != entity:
            if len(names):
                yield names
            names = set()
        entity = uri
        names.add(row.get('name'))
    if len(names):
        yield names


def normalize(text):
    text = ascii_text(text)
    text = text.replace("'", '')
    return text


@click.command()
def aggregate():
    engine = get_db()
    table = engine.get_table('tokens')
    table.delete()
    bulk = ChunkedInsert(table, chunksize=10000)
    rex = re.compile(r'\w+')
    for names in iter_names(engine):
        parts = set()
        for name in names:
            for token in rex.findall(name):
                token = token.lower()
                if len(token) > 3:
                    parts.add(token)
        pairs = set()
        for pair in combinations(parts, 2):
            pairs.add(tuple(sorted(pair)))
        for (a, b) in pairs:
            an = normalize(a)
            bn = normalize(b)
            if an == bn:
                continue
            max_dist = max(len(an), len(bn)) * 0.6
            dist = distance(an, bn)
            if dist <= max_dist:
                print(a, b, max_dist, dist, dist > max_dist)
                bulk.insert({
                    'a': a,
                    'an': an,
                    'b': b,
                    'bn': bn,
                })
    bulk.flush()


if __name__ == '__main__':
    aggregate()
