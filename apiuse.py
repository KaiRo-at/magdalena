# Example file for Socorro API use with Python

from __future__ import print_function  # to make print available in py3
from pprint import pprint  # pretty print python objects

import time
import urllib
import json
import requests

BASE_URL = 'https://crash-stats.mozilla.com/api/SuperSearch/'

datafilename = 'apitest-DATE.json'

# Run the actual meat of the script.
def run(*args):
    if args:
        version = args[0]
    else:
        version = '46.0a1'

    curtime = time.gmtime()
    timestring  = time.strftime('%Y-%m-%d', curtime)
    todayfname = datafilename.replace('DATE', timestring)

    try:
        with open(todayfname, 'r') as infile:
          testdata = json.load(infile)
    except IOError:
        testdata = {}

    urlparams = {
        'product': 'Firefox',
        'version': version,
        '_columns': [
            'date', 'signature', 'product', 'version', 'build_id', 'platform'
        ],
        '_results_number': 10,
        '_facets_size': 10
    }
    url = BASE_URL + '?' + urllib.urlencode(urlparams, True)
    print(url)

    response = requests.get(url)
    results = response.json()
    print("TOTAL")
    pprint(results['total'])
    print("HITS")
    pprint(results['hits'])
    print("SIGNATURE FACET")
    pprint(results['facets']['signature'])

    testdata[version] = {
        'total': results['total'],
        'signatures_top10': results['facets']['signature']
    }

    # Write signatures to a file.
    with open(todayfname, 'w') as outfile:
        json.dump(testdata, outfile)


# Avoid running the script when e.g. simply importing the file.
if __name__ == '__main__':
    import sys
    sys.exit(run(*sys.argv[1:]))
