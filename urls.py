from django.conf.urls.defaults import *

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
    (r'^$', 'django_schedule.views.home'),

    (r'^schedule/$', 'django_schedule.views.main_handler'),

    # TODO: I forgot some Django urlconf Zen. God will forgive, i won't.

    (r'^schedule/([^/]+)/([^/]+)/([^/]+)/$',
        'django_schedule.views.schedule_common', {'week_txt': 'both'}),

    (r'^schedule/([^/]+)/([^/]+)/([^/]+)/ical$',
     'django_schedule.views.icalendar_common', {'week_txt': 'both'}),


    (r'^schedule/([^/]+)/([^/]+)/([^/]+)/today/$',
        'django_schedule.views.today'),

    (r'^schedule/([^/]+)/([^/]+)/([^/]+)/today/ical$',
     'django_schedule.views.icalendar_common', {'week_txt': 'current', 'day_txt': 'today'}),

    # TODO match both|upper|lower
    (r'^schedule/([^/]+)/([^/]+)/([^/]+)/([^/]+)/$',
        'django_schedule.views.schedule_common'),

    (r'^schedule/([^/]+)/([^/]+)/([^/]+)/([^/]+)/ical$',
     'django_schedule.views.icalendar_common'),

    # TODO match both|upper|lower
    (r'^schedule/([^/]+)/([^/]+)/([^/]+)/([^/]+)/([^/]+)/$',
        'django_schedule.views.schedule_common'),

    (r'^schedule/([^/]+)/([^/]+)/([^/]+)/([^/]+)/([^/]+)/ical$',
     'django_schedule.views.icalendar_common'),

)
