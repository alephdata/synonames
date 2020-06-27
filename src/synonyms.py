# import math
# import phonetics
# import Levenshtein
from collections import defaultdict
from common import get_db, normalize, load_distinct, load_ignore
from common import DATA_DIR

# FORMAT
# https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-synonym-tokenfilter.html

CUTOFF = 10
QUERY = """SELECT
        a AS word,
        b AS syno,
        COUNT(*) AS num
    FROM tokens
    GROUP BY a, b
    HAVING COUNT(*) > %s
    ORDER BY COUNT(*) DESC
;""" % CUTOFF


def export():
    engine = get_db()
    # max_num = None
    distinct = load_distinct()
    ignore = load_ignore()
    synonyms_path = DATA_DIR.joinpath('synonyms.txt')
    expand = defaultdict(dict)
    with open(synonyms_path, 'w') as fh:
        for row in engine.query(QUERY):
            num = row.get('num')
            # if max_num is None:
            #     max_num = num
            word = row.get('word')[:250]
            syno = row.get('syno')[:250]

            word_n = normalize(word)
            # word_p = phonetics.soundex(word_n)
            syno_n = normalize(syno)
            # syno_p = phonetics.soundex(syno_n)
            if word_n in ignore or syno_n in ignore:
                continue
            if (word_n, syno_n) in distinct:
                continue
            # base = max(len(word_p), len(syno_p))
            # dist = Levenshtein.distance(word_p, syno_p)
            # weight = ((num - CUTOFF) / (max_num - CUTOFF))
            # weight = 1 - (math.log2(num) / math.log2(max_num))
            # ratio = (1 - (dist / base)) * weight
            # if ratio < 0.4:
            #     print(num, dist, '%.3f' % ratio,
            #           word_n, word_p, syno_n, syno_p)
            expand[word].setdefault(syno, 0)
            expand[word][syno] += num
            expand[syno].setdefault(word, 0)
            expand[syno][word] += num
            fh.write('%s, %s\n' % (word, syno))

    expand_path = DATA_DIR.joinpath('synonyms.expand.txt')
    with open(expand_path, 'w') as fh:
        for name, matches in sorted(expand.items()):
            expansions = ' , '.join(matches.keys())
            fh.write('%s => %s\n' % (name, expansions))


if __name__ == '__main__':
    export()
