# Example file for Socorro API use with Python

from __future__ import print_function  # to make print available in py3
from pprint import pprint  # pretty print python objects

import datetime
import os
import urllib
import json
import requests
from collections import OrderedDict
import re

from datautils import API_URL, global_defaults, getMaxBuildAge, getDataPath, dayList

# *** data gathering variables ***

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
    forced_dates = []

    datapath = getDataPath()
    if datapath is None:
        print('ERROR: No data path found, aborting!')
        import sys
        sys.exit(1)
    os.chdir(datapath);

    # Get platforms
    url = API_URL + 'Platforms/'
    response = requests.get(url)
    results = response.json()
    platforms = []
    for plt in results:
        platforms.append(plt["name"])

    # Get all versions
    url = API_URL + 'CurrentVersions/'
    response = requests.get(url)
    all_versions = response.json()

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

            maxday = None

            max_build_age = getMaxBuildAge(channel, True)

            for anaday in dayList(backlog_days):
                # Do not fetch data when we already have data for this day (unless it's a forced date).
                if anaday not in forced_dates and anaday in prodtypedata and prodtypedata[anaday]['adi']:
                    continue

                print('Fetching ' + product + ' ' + channel.capitalize() + ' per-type daily data for ' + anaday)

                # Could use build ID and directly go to Super Search but then we'd need to be able to match ADI with build IDs.
                # For now, we don't use that and query versions instead. This would need a False flag on getMaxBuildAge.
                #min_buildid = (datetime.datetime.strptime(anaday, '%Y-%m-%d') - max_build_age).strftime('%Y%m%d000000')

                # Get version list for this day, product and channel.
                # This can contain more versions that we have data for, so don't exactly put this into the output!
                min_verstartdate = (datetime.datetime.strptime(anaday, '%Y-%m-%d') - max_build_age).strftime('%Y-%m-%d')
                versions = []
                verinfo = {}
                for ver in all_versions:
                    if ver['product'] == product and ver['release'] == channel and ver['start_date'] > min_verstartdate:
                        versions.append(ver['version'])
                        verinfo[ver['version']] = {'tfactor': 100 / ver['throttle']}

                # Get ADI data.
                adi = {}
                urlparams = {
                    'product': product,
                    'versions': versions,
                    'start_date': anaday,
                    'end_date': anaday,
                    'platforms': platforms,
                }
                url = API_URL + 'ADI/?' + urllib.urlencode(urlparams, True)
                response = requests.get(url)
                results = response.json()
                for adidata in results['hits']:
                   adi[adidata['version']] = adidata['adi_count']

                # Get crash data.
                urlparams = {
                    'product': product,
                    'version': versions,
                    'date': ['>=' + anaday,
                             '<' + (datetime.datetime.strptime(anaday, '%Y-%m-%d') + datetime.timedelta(days=1)).strftime('%Y-%m-%d')],
                    '_aggs.version': ['process_type', 'plugin_hang'],
                    '_results_number': 0,
                }
                url = API_URL + 'SuperSearch/?' + urllib.urlencode(urlparams, True)
                response = requests.get(url)
                results = response.json()
                bytypedata = { 'versions': [], 'adi': 0, 'crashes': {}}
                for vdata in results['facets']['version']:
                    # only add the count for this version if the version has ADI.
                    if vdata['term'] in versions and vdata['term'] in adi:
                        bytypedata['versions'].append(vdata['term'])
                        bytypedata['adi'] += adi[vdata['term']]
                        nonbrowser = 0
                        for hdata in vdata['facets']['plugin_hang']:
                            if hdata['term'] == 'T':
                                if 'Hang Plugin' not in bytypedata['crashes']:
                                    bytypedata['crashes']['Hang Plugin'] = 0
                                bytypedata['crashes']['Hang Plugin'] += hdata['count'] * verinfo[vdata['term']]['tfactor']
                        for pdata in vdata['facets']['process_type']:
                            if pdata['term'] == 'plugin':
                                pname = 'OOP Plugin'
                            else:
                                pname = pdata['term'].capitalize()
                            if pname not in bytypedata['crashes']:
                                bytypedata['crashes'][pname] = 0
                            bytypedata['crashes'][pname] += pdata['count'] * verinfo[vdata['term']]['tfactor']
                            nonbrowser += pdata['count']
                        if 'Browser' not in bytypedata['crashes']:
                            bytypedata['crashes']['Browser'] = 0
                        bytypedata['crashes']['Browser'] += (vdata['count'] - nonbrowser) * verinfo[vdata['term']]['tfactor']
                if 'OOP Plugin' in bytypedata['crashes'] and 'Hang Plugin' in bytypedata['crashes']:
                    bytypedata['crashes']['OOP Plugin'] -= bytypedata['crashes']['Hang Plugin']
                bytypedata['versions'].sort()
                if bytypedata['adi']:
                    prodtypedata[anaday] = bytypedata

            # Sort and write data back to the file.
            ptd_sorted = OrderedDict(sorted(prodtypedata.items(), key=lambda t: t[0]))
            with open(fprodtypedata + '.new', 'w') as outfile:
                json.dump(ptd_sorted, outfile)


# Avoid running the script when e.g. simply importing the file.
if __name__ == '__main__':
    import sys
    sys.exit(run(*sys.argv[1:]))
