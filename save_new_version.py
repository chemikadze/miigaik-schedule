import logging
from sources.datamodel import GroupId, LOWER_WEEK, UPPER_WEEK
from sources.versions import CURRENT_SOURCE
from sources.gsql_datastore import GsqlDataSource
from sources import mock

def main():
    site_ds = CURRENT_SOURCE()
    #site_ds = mock.MockDataSource()
    collected = []
    for faculty in site_ds.faculties():
        for year in site_ds.years():
            for group in site_ds.groups():
                if site_ds.valid_comp(year, group):
                    gid = GroupId(faculty['value'], year['value'], group['value'])
                    collected.append(site_ds.group_data(gid))
    new_v = GsqlDataSource.save_new_version(site_ds.groups(),
                                            site_ds.faculties(),
                                            site_ds.years(),
                                            collected)
    print 'Fetched new version %s' % new_v


if __name__ == '__main__':
    try:
        main()
    except Exception:
        logging.exception("Exception during update: ")
