from django.conf.urls.defaults import *
import django_schedule

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
from sources.datamodel import UPPER_WEEK, LOWER_WEEK, GroupId, ClassroomId

urlpatterns = patterns('',
    (r'^$', 'django_schedule.views.home'),

    (r'^schedule/$', 'django_schedule.views.main_handler'),

    # TODO: I forgot some Django urlconf Zen. God will forgive, i won't.

    (r'^schedule/(?P<faculty>.+)\|(?P<year>.+)\|(?P<group>.+)\|data/',
        include('django_schedule.generic_urls'),
         {'method': 'group_data', 'id_factory': GroupId, 'template': 'student'}),

    (r'^classrooms/(?P<building>.+)\|(?P<number>.+)\|data/',
     include('django_schedule.generic_urls'),
        {'method': 'classroom_data', 'id_factory': ClassroomId, 'template': 'auditory'}),

    (r'^classrooms/free/', 'django_schedule.views.free_classrooms'),

    (r'^api/rasp-vuzov/', include('rasp_vuzov_api.urls')),

    (r'^rest/', include('django_schedule.urls'))
)
