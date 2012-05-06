from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
from sources.datamodel import UPPER_WEEK, LOWER_WEEK, GroupId, ClassroomId

urlpatterns = patterns('',

    # TODO: I forgot some Django urlconf Zen. God will forgive, i won't.

    (r'^$',
     'django_schedule.views.generic_schedule_common',
         {'week_txt': 'both'}),

    (r'^ical$',
     'django_schedule.views.icalendar_common',
         {'week_txt': 'both'}),


    (r'^today/$',
     'django_schedule.views.generic_today'),

    (r'^today/ical$',
     'django_schedule.views.icalendar_common',
        {'week_txt': 'current', 'day_txt': 'today'}),

    # TODO match both|upper|lower
    (r'^(?P<week_txt>[^/]+)/$',
     'django_schedule.views.generic_schedule_common'),

    (r'^(?P<week_txt>[^/]+)/ical$',
     'django_schedule.views.icalendar_common'),

    # TODO match both|upper|lower
    (r'^(?P<week_txt>[^/]+)/(?P<day_txt>[^/]+)/$',
     'django_schedule.views.generic_schedule_common'),

    (r'^(?P<week_txt>[^/]+)/(?P<day_txt>[^/]+)/ical$',
     'django_schedule.views.icalendar_common')
)
