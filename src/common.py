import os
import dataset


def get_db():
    db_uri = os.environ.get('DATABASE_URI')
    return dataset.connect(db_uri)
