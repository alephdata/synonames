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
    HAVING COUNT(*) > 30
    ORDER BY COUNT(*) DESC
;"""


@click.command()
def export():
    engine = get_db()
    mappings = defaultdict(set)
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
            if name == unique:
                continue
            mappings[name].add(canonical)

        # num = row.get('num')
        # meta = '# %s <(%s)> %s\n' % (an, num, bn)
        # fh.write(meta)
        # synonyms = ' , '.join(unique)
        # fh.write('%s => %s\n\n' % (synonyms, canonical))

    with open('synonyms.txt', 'w') as fh:
        for name, expansions in mappings.items():
            expansions = ' , '.join(expansions)
            fh.write('%s => %s\n' % (name, expansions))
            # print(name, expansions)


if __name__ == '__main__':
    export()
