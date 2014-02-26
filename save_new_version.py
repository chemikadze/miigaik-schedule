import logging

from google.appengine.api import memcache

from sources.datamodel import GroupId, LOWER_WEEK, UPPER_WEEK
from sources.util import empty_data
from sources.versions import CURRENT_SOURCE
from sources.gsql_datastore import GsqlDataSource
from sources import mock

class Terminate(Exception): pass

def main():
    site_ds = CURRENT_SOURCE()
    #site_ds = mock.MockDataSource()
    collected = []
    #c = 0
    try:
        for group in site_ds.groups():
            for faculty in site_ds.faculties():
                for year in site_ds.years():
                    if site_ds.valid_comp(year, group):
                        gid = GroupId(faculty['value'], year['value'], group['value'])
                        gdata = site_ds.group_data(gid)
                        logging.warn("%s: %s" %
                            (gid, gdata.week(UPPER_WEEK)[0][1].list()))
                        if not empty_data(gdata):
                            collected.append(site_ds.group_data(gid))
                            #if c < 2: c += 1
                            #else: raise Terminate()
    except Terminate:
        pass
    new_v = GsqlDataSource.save_new_version(site_ds.groups(),
                                            site_ds.faculties(),
                                            site_ds.years(),
                                            collected)
    memcache.flush_all()
    print 'Fetched new version %s' % new_v


if __name__ == '__main__':
    try:
        main()
    except:
        logging.exception("Exception during update: ")
