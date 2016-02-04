# Example file for Socorro API use with Python

from __future__ import print_function  # to make print available in py3
from pprint import pprint  # pretty print python objects

import datetime
import os
import urllib
import json
import requests

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

# https://crash-stats.mozilla.com/api/ADI/?end_date=2016-02-02&platforms=Windows&platforms=Linux&platforms=Mac+OS+X&product=Firefox&start_date=2016-02-01&versions=44.0

# Run the actual meat of the script.
def run():
    # Get start and end dates
    day_start = (datetime.datetime.utcnow() - datetime.timedelta(days=backlog_days)).strftime('%Y-%m-%d')
    day_end = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    pprint(day_start)
    pprint(day_end)

    datapath = getDataPath()
    if datapath is None:
        print('ERROR: No data path found, aborting!')
        import sys
        sys.exit(1)
    os.chdir(datapath);

    pprint(datapath)
    pprint(API_URL)

    # Daily data
    for product in products:
        fproddata = product + '-daily.json'

        try:
            with open(fproddata, 'r') as infile:
                print('Read stored ' + product + ' daily data')
                proddata = json.load(infile)
        except IOError:
            proddata = {}

        print('Fetch daily data for ' + product + ' ' + 'version, version, ...')

        # Actually get the data.


        # Write data back to the file.
        with open(fproddata, 'w') as outfile:
            json.dump(proddata, outfile)


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


            # Write data back to the file.
            with open(fprodtypedata, 'w') as outfile:
                json.dump(prodtypedata, outfile)


# Avoid running the script when e.g. simply importing the file.
if __name__ == '__main__':
    import sys
    sys.exit(run(*sys.argv[1:]))
