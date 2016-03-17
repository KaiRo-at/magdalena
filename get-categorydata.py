# Example file for Socorro API use with Python

from __future__ import print_function  # to make print available in py3
from pprint import pprint  # pretty print python objects

import datetime
import os
import json
from collections import OrderedDict
import re

from datautils import (getFromAPI, global_defaults, verifyForcedDates,
                       getMaxBuildAge, getDataPath, dayList,
                       dayStringBeforeDelta, dayStringAdd)

# *** data gathering variables ***

# products and channels to gather data per-type from
prodchannels = {
  'Firefox': ['release', 'beta', 'aurora', 'nightly'],
  'FennecAndroid': ['release', 'beta', 'aurora', 'nightly']
}

# reports to process
reports = {
  'startup': {
    'params': {
      'uptime': '<60',
    },
    'process_split': True,
    'desktoponly': False,
  },
  'oom': {
    'params': {
      'signature': ['^js::AutoEnterOOMUnsafeRegion::crash', '^OOM |'],
    },
    'process_split': True,
    'desktoponly': False,
  },
  'oom:small': {
    'params': {
      'signature': '=OOM | small',
    },
    'process_split': True,
    'desktoponly': False,
  },
  'oom:large': {
    'params': {
      'signature': '^OOM | large |',
    },
    'process_split': True,
    'desktoponly': False,
  },
  'shutdownhang': {
    'params': {
      'signature': '^shutdownhang |',
    },
    'process_split': False,
    'desktoponly': True,
  },
  'address:pure': {
    # The signature starts with a "pure" @0xFOOBAR address but not with a prepended "@0x0 |".
    'params': {
      # This doesn't work, see https://bugzilla.mozilla.org/show_bug.cgi?id=1257376
      #'signature': ['^@0x', '!^@0x0 |'],
      # For now, take advantage of a leading 0 in addresses is not displayed and include the exact bare @0x0.
      'signature': ['=@0x0','^@0x1','^@0x2','^@0x3','^@0x4','^@0x5','^@0x6','^@0x7','^@0x8','^@0x9','^@0xa','^@0xb','^@0xc','^@0xd','^@0xe','^@0xf'],
    },
    'process_split': True,
    'desktoponly': True,
  },
#  'address:file': {
#    # The signature starts with a non-symbolized file@0xFOOBAR piece (potentially after a @0x0 frame).
#    #'filter' => "split_part(regexp_replace(signatures.signature, '^@0x0 \| ', ''), ' | ', 1) LIKE '%_@0x%'",
#    'params': {
#      #This case can't be done with Super Search right now, see https://bugzilla.mozilla.org/show_bug.cgi?id=1257382
#      'signature': '/^(@0x0 \| )?[^@\|]+@0x/',
#    },
#    'process_split': True,
#    'desktoponly': True,
#  },
}

# for how many days back to get the data
backlog_days = global_defaults['socorrodata_backlog_days']

# *** URLs and paths ***

# Run the actual meat of the script.
def run(*args):
    forced_dates = verifyForcedDates(args)
    anadayList = dayList(backlog_days, forced_dates)

    datapath = getDataPath()
    if datapath is None:
        print('ERROR: No data path found, aborting!')
        import sys
        sys.exit(1)
    os.chdir(datapath);

    # Get a minimum start date older than any needed below:
    # 1) First element in the anadayList is the earlist day we build stuff for.
    # 2) For unknown channels, getMaxBuildAge returns a larger age value than for anything else.
    earliest_mindate = dayStringBeforeDelta(anadayList[0], getMaxBuildAge('none'))
    # Get all possibly needed versions for all products we look for.
    all_versions = getFromAPI('ProductVersions', {
        'product': prodchannels.keys(),
        'start_date': '>' + earliest_mindate,
        'is_rapid_beta': 'false',
    })['hits']

    # Get daily category data
    for (product, channels) in prodchannels.items():
        for channel in channels:
            fprodcatdata = product + '-' + channel + '-crashes-categories.json'
            fprodtypedata = product + '-' + channel + '-crashes-bytype.json'

            try:
                with open(fprodcatdata, 'r') as infile:
                    print('Read stored ' + product + ' ' + channel.capitalize() + ' category data')
                    prodcatdata = json.load(infile)
            except IOError:
                prodcatdata = {}

            try:
                with open(fprodtypedata, 'r') as infile:
                    print('Read stored ' + product + ' ' + channel.capitalize() + ' per-type data')
                    prodtypedata = json.load(infile)
            except IOError:
                prodtypedata = {}

            maxday = None

            max_build_age = getMaxBuildAge(channel, True)

            for anaday in anadayList:
                # Do not fetch data when we already have data for this day (unless it's a forced date) or if we don't have by-type data.
                if (anaday not in forced_dates and anaday in prodcatdata) or anaday not in prodtypedata:
                    continue

                print('Category Counts: Looking at category data for ' + product + ' ' + channel.capitalize() + ' on ' + anaday)

                # Could use build ID and directly go to Super Search but then we'd need to be able to match ADI with build IDs.
                # For now, we don't use that and query versions instead. This would need a False flag on getMaxBuildAge.
                #min_buildid = (datetime.datetime.strptime(anaday, '%Y-%m-%d') - max_build_age).strftime('%Y%m%d000000')

                # Get version list for this day, product and channel.
                # This can contain more versions that we have data for, so don't exactly put this into the output!
                min_verstartdate = dayStringBeforeDelta(anaday, max_build_age)
                versions = []
                verinfo = {}
                for ver in all_versions:
                    if ver['product'] == product and ver['build_type'] == channel and ver['start_date'] > min_verstartdate:
                        versions.append(ver['version'])
                        verinfo[ver['version']] = {'tfactor': 100 / ver['throttle']}

                catdata = {}
                allcount = 0
                for (catname, rep) in reports.items():
                    if rep['desktoponly'] and product != 'Firefox':
                        continue
                    print('    * ' + catname)

                    # Get crash data.
                    ssparams = {
                        'product': product,
                        'version': versions,
                        'date': ['>=' + anaday,
                                '<' + dayStringAdd(anaday, days=1)],
                        '_aggs.version': ['process_type'],
                        '_results_number': 0,
                        '_facets': 'process_type',
                    }
                    ssparams.update(rep['params'])
                    results = getFromAPI('SuperSearch', ssparams)
                    if rep['process_split']:
                        catdata[catname] = {}
                        for vdata in results['facets']['version']:
                            nonbrowser = 0
                            for pdata in vdata['facets']['process_type']:
                                if pdata['term'] not in catdata[catname]:
                                    catdata[catname][pdata['term']] = 0
                                catdata[catname][pdata['term']] += pdata['count'] * verinfo[vdata['term']]['tfactor']
                                nonbrowser += pdata['count']
                            if 'browser' not in catdata[catname]:
                                catdata[catname]['browser'] = 0
                            catdata[catname]['browser'] += (vdata['count'] - nonbrowser) * verinfo[vdata['term']]['tfactor']
                            allcount += vdata['count']
                    else:
                        catdata[catname] = 0
                        for vdata in results['facets']['version']:
                            catdata[catname] += vdata['count'] * verinfo[vdata['term']]['tfactor']
                            allcount += vdata['count']
                if allcount:
                    prodcatdata[anaday] = catdata

            # Sort and write data back to the file.
            ptd_sorted = OrderedDict(sorted(prodcatdata.items(), key=lambda t: t[0]))
            with open(fprodcatdata, 'w') as outfile:
                json.dump(ptd_sorted, outfile)


# Avoid running the script when e.g. simply importing the file.
if __name__ == '__main__':
    import sys
    sys.exit(run(*sys.argv[1:]))
