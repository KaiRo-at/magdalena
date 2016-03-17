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

def dayList(backlog_days, forced_dates = None):
    from datetime import datetime, timedelta
    import re
    forced_dates = forced_dates or []
    days_to_analyze = [];
    for daysback in xrange(backlog_days):
        days_to_analyze.append(beforeTodayString(days=daysback))
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

def getFromAPI(api, params = None):
    import urllib
    import requests
    url = API_URL + api + '/'
    if params:
        url += '?' + urllib.urlencode(params, True)
    #print(url)
    response = requests.get(url)
    return response.json()

def verifyForcedDates(fdates):
    from datetime import datetime
    import re
    force_dates = [];
    for fdate in fdates:
        if (re.match(r"\d+-\d+-\d+", fdate) and
            datetime.strptime(fdate, '%Y-%m-%d').strftime('%Y-%m-%d') == fdate):
            force_dates.append(fdate);
    return force_dates

def beforeTodayString(days = 0, weeks = 0):
    from datetime import datetime, timedelta
    return (datetime.utcnow() - timedelta(days=days, weeks=weeks)).strftime('%Y-%m-%d')

def dayStringAdd(anaday, days = 0, weeks = 0):
    from datetime import datetime, timedelta
    return (datetime.strptime(anaday, '%Y-%m-%d') + timedelta(days=days, weeks=weeks)).strftime('%Y-%m-%d')

def dayStringBeforeDelta(anaday, tdelta):
    from datetime import datetime
    return (datetime.strptime(anaday, '%Y-%m-%d') - tdelta).strftime('%Y-%m-%d')
