from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
from sources.datamodel import UPPER_WEEK, LOWER_WEEK

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'django_schedule.views.home', name='home'),
    # url(r'^django_schedule/', include('django_schedule.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'django_schedule.views.home'),

    url(r'^schedule/$', 'django_schedule.views.main_handler'),

    url(r'^schedule/([^/]+)/([^/]+)/([^/]+)/$', 'django_schedule.views.week_schedule'),
    url(r'^schedule/([^/]+)/([^/]+)/([^/]+)/both/$', 'django_schedule.views.week_schedule'),
    url(r'^schedule/([^/]+)/([^/]+)/([^/]+)/upper/$',
        'django_schedule.views.week_schedule', {'week': UPPER_WEEK}),
    url(r'^schedule/([^/]+)/([^/]+)/([^/]+)/lower/$',
        'django_schedule.views.week_schedule', {'week': LOWER_WEEK}),
    url(r'^schedule/([^/]+)/([^/]+)/([^/]+)/both/([^/]+)/$', 'django_schedule.views.day_schedule'),
    url(r'^schedule/([^/]+)/([^/]+)/([^/]+)/upper/([^/]+)/$',
        'django_schedule.views.day_schedule', {'week': UPPER_WEEK}),
    url(r'^schedule/([^/]+)/([^/]+)/([^/]+)/lower/([^/]+)/$',
        'django_schedule.views.day_schedule', {'week': LOWER_WEEK})

)
