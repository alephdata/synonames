import re
# import json
import click
from Levenshtein import distance
from itertools import combinations
from dataset.chunked import ChunkedInsert
from common import get_db, normalize

# Filter out non-latin alphabets that we don't support in
# other parts of the stack anyway and that will not well
# survive transliteration:
SKIP_LANGUAGES = set([
    'ast', 'ja', 'zh', 'zh-hant', 'zh-hk', 'ko',
    'id', 'th', 'ia', 'gan', 'si', 'zh-classical',
    'nv', 'or', 'arc', 'cu', 'lo', 'iu', 'got',
    'chr', 'cr', 'bug', 'dz', 'gom', 'tcy', 'dty',
    'sat', 'nqo', 'mnw', 'pi', 'shn', 'ii',  'hi',
    'bn', 'te', 'mr', 'gu', 'ta', 'zh-yue', 'my',
    'gu', 'kn', 'ml', 'ne', 'pa', 'as', 'new',
    'bpy', 'sa', 'mai', 'wuu', 'km', 'am', 'dv',
])


def iter_names(engine):
    table = engine.get_table('names')
    entity = None
    names = set()
    for row in table.find(order_by='uri'):
        if row.get('lang') in SKIP_LANGUAGES:
            continue
        uri = row.get('uri')
        entity = entity or uri
        if uri != entity:
            if len(names):
                yield names
            names = set()
        entity = uri
        names.add(row.get('name'))
    if len(names) > 1:
        yield names


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
                    norm = normalize(token)
                    if len(norm):
                        parts.add((token, norm))
        pairs = set()
        for pair in combinations(parts, 2):
            pairs.add(tuple(sorted(pair)))
        for ((a, an), (b, bn)) in pairs:
            if an == bn:
                continue
            max_dist = max(len(an), len(bn)) * 0.6
            dist = distance(an, bn)
            if dist <= max_dist:
                # print(a, b, max_dist, dist, dist > max_dist)
                bulk.insert({
                    'a': a,
                    'an': an,
                    'b': b,
                    'bn': bn,
                })
    bulk.flush()


if __name__ == '__main__':
    aggregate()
