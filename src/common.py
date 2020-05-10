import os
import dataset
from pathlib import Path


def get_db():
    db_uri = os.environ.get('DATABASE_URI')
    return dataset.connect(db_uri)


# Folder set-up:
CODE_DIR = Path(os.path.dirname(__file__)).resolve()
DATA_DIR = CODE_DIR.joinpath('../data/output').resolve()
DATA_DIR.mkdir(exist_ok=True, parents=True)
