# Example file for Socorro API use with Python

from __future__ import print_function  # to make print available in py3
from pprint import pprint  # pretty print python objects

import json
import requests

baseURL = (
    'https://crash-stats.mozilla.com/api/SuperSearch/?product=Firefox&version=VERSION'
    '&_facets=signature&_columns=date&_columns=signature&_columns=product'
    '&_columns=version&_columns=build_id&_columns=platform'
    '&_results_number=10&_facets_size=10'
)

outfilename = 'apitest-VERSION.json'

# Run the actual meat of the script.
def run(*args):
    if args:
        version = args[0]
    else:
        version = '46.0a1'

    url = baseURL.replace('VERSION', version)
    print(url)

    response = requests.get(url)
    results = response.json()
    print("TOTAL")
    pprint(results['total'])
    print("HITS")
    pprint(results['hits'])
    print("SIGNATURE FACET")
    pprint(results['facets']['signature'])

    # Write signatures to a file.
    with open(outfilename.replace('VERSION', version), 'w') as outfile:
        json.dump(results['facets']['signature'], outfile)


# Avoid running the script when e.g. simply importing the file.
if __name__ == '__main__':
    import sys
    sys.exit(run(*sys.argv[1:]))
