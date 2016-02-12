# Example file for Socorro API use with Python

from __future__ import print_function  # to make print available in py3
from pprint import pprint  # pretty print python objects

import datetime
import os
import json
from collections import OrderedDict

from datautils import (getFromAPI, global_defaults, getDataPath,
                       beforeTodayString)

# *** data gathering variables ***

# products to gather data from
products = ['Firefox', 'FennecAndroid']

# for how many days back to get the data
backlog_days = global_defaults['socorrodata_backlog_days'];

# *** URLs and paths ***

# Run the actual meat of the script.
def run():
    # Get start and end dates
    day_start = beforeTodayString(days=backlog_days)
    day_end = beforeTodayString(days=1)

    datapath = getDataPath()
    if datapath is None:
        print('ERROR: No data path found, aborting!')
        import sys
        sys.exit(1)
    os.chdir(datapath);

    for product in products:
        fproddata = product + '-daily.json'

        try:
            with open(fproddata, 'r') as infile:
                print('Read stored ' + product + ' daily data')
                proddata = json.load(infile)
        except IOError:
            proddata = {}

        # Get all active versions for that product.
        ver_results = getFromAPI('CurrentVersions')
        versions = []
        verinfo = {}
        for ver in ver_results:
            if ver['product'] == product and ver['end_date'] > day_start:
                versions.append(ver['version'])
                verinfo[ver['version']] = {'tfactor': 100 / ver['throttle']}

        print('Fetch daily data for ' + product + ' ' + ', '.join(versions))

        # Get data for those versions and days.
        maxday = None

        results = getFromAPI('CrashesPerAdu', {
            'product': product,
            'versions': versions,
            'from_date': day_start,
            'to_date': day_end,
        })
        for (pver, pvdata) in results['hits'].items():
            for (day, pvd) in pvdata.items():
                ver = pvd['version']
                crashes = pvd['report_count'] * verinfo[ver]['tfactor']
                adu = pvd['adu']
                if crashes or adi:
                    if ver not in proddata:
                        proddata[ver] = {}
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


# Avoid running the script when e.g. simply importing the file.
if __name__ == '__main__':
    import sys
    sys.exit(run(*sys.argv[1:]))
