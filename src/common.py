import os
import string
import dataset
from pathlib import Path
from normality import ascii_text

ALPHABET = string.ascii_letters + string.digits

# Folder set-up:
CODE_DIR = Path(os.path.dirname(__file__)).resolve()
DATA_DIR = CODE_DIR.joinpath('../data/output').resolve()
DATA_DIR.mkdir(exist_ok=True, parents=True)


def get_db():
    db_uri = os.environ.get('DATABASE_URI')
    return dataset.connect(db_uri)


def normalize(text):
    text = ascii_text(text)
    passed = [c for c in text if c in ALPHABET]
    # text = text.replace("'", '')
    return ''.join(passed)


def load_distinct():
    distinct_txt = CODE_DIR.joinpath('distinct.txt')
    pairs = set()
    with open(distinct_txt, 'r') as fh:
        for line in fh.readlines():
            fst, snd = line.split(', ', 1)
            fst_n = normalize(fst)
            snd_n = normalize(snd)
            pairs.add((fst_n, snd_n))
            pairs.add((snd_n, fst_n))
    return pairs


def load_ignore():
    ignore_txt = CODE_DIR.joinpath('ignore.txt')
    ignores = set()
    with open(ignore_txt, 'r') as fh:
        for line in fh.readlines():
            ignores.add(normalize(line))
    return ignores
