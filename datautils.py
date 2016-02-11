# Variables and utility functions used by multiple other scripts.

API_URL = 'https://crash-stats.mozilla.com/api/'
global_defaults = {
    'backlog_days': 7,
    'explosive_backlog_days': 20,
    'socorrodata_backlog_days': 15,
}

def getMaxBuildAge(channel, version_overall = False):
    import datetime
    if channel == 'release':
        return datetime.timedelta(weeks=12)
    elif channel == 'beta':
        return datetime.timedelta(weeks=4)
    elif channel == 'aurora':
        if version_overall:
            return datetime.timedelta(weeks=9)
        else:
            return datetime.timedelta(weeks=2)
    elif channel == 'nightly':
        if version_overall:
            return datetime.timedelta(weeks=9)
        else:
            return datetime.timedelta(weeks=1)
    else:
        return datetime.timedelta(days=365); # almost forever

def dayList(backlog_days, forced_dates = []):
    import datetime
    import re
    days_to_analyze = [];
    for daysback in xrange(backlog_days):
        days_to_analyze.append((datetime.datetime.utcnow() - datetime.timedelta(days=daysback)).strftime('%Y-%m-%d'))
    for anaday in forced_dates:
        if re.match(r"\d+-\d+-\d+", anaday) and anaday not in days_to_analyze:
            days_to_analyze.append(anaday)
    days_to_analyze.sort()
    return days_to_analyze

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
