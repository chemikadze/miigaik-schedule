import mock
import versions
import gsql_datastore

#CURRENT_SOURCE = versions.CURRENT_SOURCE
#CURRENT_SOURCE = mock.MockDataSource
CURRENT_SOURCE = gsql_datastore.GsqlDataSource