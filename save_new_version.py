import logging
import os
import sys

from google.appengine.api import memcache

ROOT_PATH = os.path.dirname(__file__)
sys.path.append(ROOT_PATH)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gaenv'))

import settings
from sources.datamodel import UPPER_WEEK
from sources.util import empty_data
from sources.versions import CURRENT_SOURCE
from sources.gsql_datastore import GsqlDataSource


def main():
    site_ds = getattr(settings, 'IMPORT_SOURCE', None)
    logging.info(site_ds)
    if not site_ds:
        site_ds = CURRENT_SOURCE()
    max_groups = getattr(settings, 'MAX_GROUPS', 0)
    collected = []
    c = 0
    for (gid, gname) in site_ds.group_ids():
            gdata = site_ds.group_data(gid)
            logging.info("%s: %s" %
                (gid, gdata.week(UPPER_WEEK)[0][1].list()))
            if not empty_data(gdata):
                collected.append(site_ds.group_data(gid))
                if max_groups:
                    if c < max_groups:
                        c += 1
                    else:
                        break

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
