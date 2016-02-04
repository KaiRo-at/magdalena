# Variables and utility functions used by multiple other scripts.

API_URL = 'https://crash-stats.mozilla.com/api/'
global_defaults = {
    'backlog_days': 7,
    'explosive_backlog_days': 20,
    'socorrodata_backlog_days': 15,
}

def getMaxBuildAge(channel, version_overall = False):
    if channel == 'release':
        return '12 weeks'
    elif channel == 'beta':
        return '4 weeks'
    elif channel == 'aurora':
        if version_overall:
            return '9 weeks'
        else:
            return '2 weeks'
    elif channel == 'nightly':
        if version_overall:
            return '9 weeks'
        else:
            return '1 weeks'
    else:
        return '1 year'; # almost forever

def getDataPath():
    import os
    data_path = None
    for testpath in ['/mnt/crashanalysis/rkaiser/',
                     '/home/rkaiser/reports/',
                     '/mnt/mozilla/projects/socorro/']:
        if os.path.exists(testpath) and os.path.isdir(testpath):
            data_path = testpath
            break
    return data_path
