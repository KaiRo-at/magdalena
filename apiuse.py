# Example file for Socorro API use with Python

from __future__ import print_function

from pprint import pprint

# See http://stackoverflow.com/a/30362669/205832
import requests

URL = (
    'https://crash-stats.mozilla.com/api/SuperSearch/?product=Firefox&version=VERSION'
    '&_facets=signature&_columns=date&_columns=signature&_columns=product'
    '&_columns=version&_columns=build_id&_columns=platform'
    '&_results_number=10&_facets_size=10'
)


def run(*args):
    if args:
        version = args[0]
    else:
        version = '46.0a1'

    url = URL.replace('VERSION', version)
    print(url)

    response = requests.get(url)
    results = response.json()
    print("HITS")
    pprint(results['hits'])
    print("FACETS")
    pprint(results['facets'])

if __name__ == '__main__':
    import sys
    sys.exit(run(*sys.argv[1:]))
