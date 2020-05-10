from collections import defaultdict
from common import get_db, DATA_DIR

# FORMAT
# https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-synonym-tokenfilter.html

QUERY = """SELECT
        a AS word,
        b AS syno,
        COUNT(*) AS num
    FROM tokens
    GROUP BY a, b
    HAVING COUNT(*) > 100
    ORDER BY COUNT(*) DESC
;"""

# STOP = [
#     ('jean', 'paul'),
#     ('saud', 'aziz'),
#     ('maria', 'teresa'),
#     ('karl', 'georg'),
#     ('earl', 'george'),
#     ('lord', 'baron'),
#     ('pope', 'papa'),
#     ('anne', 'maria'),
#     ('anna', 'maria'),
#     ('vlad', 'tepes'),
#     ('xaver', 'franz'),
#     ('heinrich', 'friedrich'),
# ]


def export():
    engine = get_db()
    expand = defaultdict(set)
    synonyms_path = DATA_DIR.joinpath('synonyms.txt')
    with open(synonyms_path, 'w') as fh:
        for row in engine.query(QUERY):
            word = row.get('word')
            syno = row.get('syno')
            expand[word].add(syno)
            expand[syno].add(word)
            fh.write('%s, %s\n' % (word, syno))

    expand_path = DATA_DIR.joinpath('synonyms.expand.txt')
    with open(expand_path, 'w') as fh:
        for name, expansions in sorted(expand.items()):
            expansions = ' , '.join(expansions)
            fh.write('%s => %s\n' % (name, expansions))


if __name__ == '__main__':
    export()
