import click
from collections import defaultdict
# from Levenshtein import setmedian
from common import get_db

# FORMAT
# https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-synonym-tokenfilter.html

QUERY = """SELECT
        ARRAY_AGG(a) AS al, an,
        ARRAY_AGG(b) AS bl, bn,
        COUNT(*) AS num
    FROM tokens
    WHERE an != bn
    GROUP BY an, bn
    HAVING COUNT(*) > 10
    ORDER BY COUNT(*) DESC
;"""

STOP = [
    ('jean', 'paul'),
    ('saud', 'aziz'),
    ('maria', 'teresa'),
    ('karl', 'georg'),
    ('earl', 'george'),
    ('lord', 'baron'),
    ('pope', 'papa'),
    ('anne', 'maria'),
    ('anna', 'maria'),
    ('vlad', 'tepes'),
    ('xaver', 'franz'),
    ('heinrich', 'friedrich'),
]


@click.command()
def export():
    engine = get_db()
    mappings = defaultdict(set)
    expand = defaultdict(set)
    for row in engine.query(QUERY):
        al = row.get('al')
        # an = row.get('an')
        bl = row.get('bl')
        # bn = row.get('bn')
        synonyms = al + bl
        unique = set(synonyms)
        canonical = max(unique, key=synonyms.count)
        # canonical = setmedian(synonyms)
        # unique.remove(canonical)
        # print(unique, canonical)
        for name in unique:
            expand[name].update([u for u in unique if u != name])
            if name != canonical:
                mappings[name].add(canonical)

    with open('synonyms.txt', 'w') as fh:
        for name, expansions in sorted(mappings.items()):
            expansions = ' , '.join(expansions)
            fh.write('%s => %s\n' % (name, expansions))
            # print(name, expansions)

    with open('synonyms.expand.txt', 'w') as fh:
        for name, expansions in sorted(expand.items()):
            expansions = ' , '.join(expansions)
            fh.write('%s => %s\n' % (name, expansions))
            # print(name, expansions)


if __name__ == '__main__':
    export()
