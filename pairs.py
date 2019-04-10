import json
import click
from collections import Counter
from itertools import combinations
from normality import ascii_text


@click.command()
@click.option('-i', '--input', type=click.File('r'), default='-')  # noqa
@click.option('-o', '--output', type=click.File('w'), default='-')  # noqa
def aggregate(input, output):
    counter = Counter()
    while True:
        line = input.readline()
        if not line:
            break
        tokens = set()
        for name in json.loads(line):
            for token in name.split(' '):
                # token = ascii_text(token)
                if token and len(token) > 3:
                    token = token.replace("'", '').lower()
                    tokens.add(token)
        for (a, b) in combinations(tokens, 2):
            a, b = max([a, b]), min([a, b])
            kw = ':'.join((a, b))
            counter[kw] += 1
    print(counter.most_common(100))


if __name__ == '__main__':
    aggregate()
