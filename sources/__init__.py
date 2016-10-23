#import mock
import versions

_google_libs_missing = False
try:
    from google.appengine.ext import db
except:
    import warnings
    warnings.warn("GAE API not detected, swallowing")
    _google_libs_missing = True

if not _google_libs_missing:
    import gsql_datastore
    CURRENT_SOURCE = gsql_datastore.GsqlDataSource
else:
    CURRENT_SOURCE = versions.CURRENT_SOURCE

#CURRENT_SOURCE = versions.CURRENT_SOURCE
#CURRENT_SOURCE = mock.MockDataSource


CURRENT_TIMETABLE = versions.CURRENT_TIMETABLE
