# Example file for Socorro API use with Python

from __future__ import print_function  # to make print available in py3
from pprint import pprint  # pretty print python objects

import datetime
import os
import urllib
import json
import requests
from collections import OrderedDict

from datautils import API_URL, global_defaults, getMaxBuildAge, getDataPath

# *** data gathering variables ***

# products to gather data from
products = ['Firefox'] # ['Firefox', 'FennecAndroid']

# products and channels to gather data per-type from
prodchannels = {
  'Firefox': ['release', 'beta', 'aurora', 'nightly'],
#  'FennecAndroid': ['release', 'beta', 'aurora', 'nightly']
}

# for how many days back to get the data
backlog_days = global_defaults['socorrodata_backlog_days'];

# *** URLs and paths ***

# Run the actual meat of the script.
def run():
    # Get start and end dates
    day_start = (datetime.datetime.utcnow() - datetime.timedelta(days=backlog_days)).strftime('%Y-%m-%d')
    day_end = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    datapath = getDataPath()
    if datapath is None:
        print('ERROR: No data path found, aborting!')
        import sys
        sys.exit(1)
    os.chdir(datapath);

    # Daily data
    for product in products:
        fproddata = product + '-daily.json'

        try:
            with open(fproddata, 'r') as infile:
                print('Read stored ' + product + ' daily data')
                proddata = json.load(infile)
        except IOError:
            proddata = {}

        # Get all active versions for that product.
        url = API_URL + 'CurrentVersions/'

        response = requests.get(url)
        ver_results = response.json()
        versions = []
        verinfo = {}
        for ver in ver_results:
            if ver['product'] == product and ver['end_date'] > day_start:
                versions.append(ver['version'])
                verinfo[ver['version']] = {'tfactor': 100 / ver['throttle']}

        print('Fetch daily data for ' + product + ' ' + ', '.join(versions))

        # Get data for those versions and days.
        maxday = None

        urlparams = {
            'product': product,
            'versions': versions,
            'from_date': day_start,
            'to_date': day_end,
        }
        url = API_URL + 'CrashesPerAdu/?' + urllib.urlencode(urlparams, True)

        response = requests.get(url)
        results = response.json()
        for (pver, pvdata) in results['hits'].items():
            for (day, pvd) in pvdata.items():
                ver = pvd['version']
                crashes = pvd['report_count'] * verinfo[ver]['tfactor']
                adu = pvd['adu']
                if crashes or adi:
                    proddata[ver][day] = {'crashes': crashes, 'adu': adu}
                if maxday is None or maxday < day:
                    maxday = day
        if maxday < day_end:
            print('--- ERROR: Last day retrieved is ' + maxday + ' while yesterday was ' + day_end + '!')


        # Sort and write data back to the file.
        pd_sorted = OrderedDict()
        for version in sorted(proddata.iterkeys()):
           pd_sorted[version] = OrderedDict(sorted(proddata[version].items(), key=lambda t: t[0]))
        with open(fproddata + '.new', 'w') as outfile:
            json.dump(pd_sorted, outfile)

    # uncomment for backfilling
    #day_start = '2011-01-01';

    # https://crash-stats.mozilla.com/api/ADI/?end_date=2016-02-02&platforms=Windows&platforms=Linux&platforms=Mac+OS+X&product=Firefox&start_date=2016-02-01&versions=44.0

    # Get platforms
    url = API_URL + 'Platforms/'

    response = requests.get(url)
    results = response.json()
    platforms = []
    for plt in results:
        platforms.append(plt["name"])

    pprint(platforms)

    # By-type daily data
    for (product, channels) in prodchannels.items():
        for channel in channels:
            fprodtypedata = product + '-' + channel + '-bytype.json'

            try:
                with open(fprodtypedata, 'r') as infile:
                    print('Read stored ' + product + ' ' + channel.capitalize() + ' per-type data')
                    prodtypedata = json.load(infile)
            except IOError:
                prodtypedata = {}

            print('Fetch per-type daily data for ' + product + ' ' + channel.capitalize())

            maxday = None

            max_build_age = getMaxBuildAge(channel, True)

            # Actually get the data.


            # Sort and write data back to the file.
            ptd_sorted = OrderedDict(sorted(prodtypedata.items(), key=lambda t: t[0]))
            with open(fprodtypedata + '.new', 'w') as outfile:
                json.dump(ptd_sorted, outfile)


# Avoid running the script when e.g. simply importing the file.
if __name__ == '__main__':
    import sys
    sys.exit(run(*sys.argv[1:]))
