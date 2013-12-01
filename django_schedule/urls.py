from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',

    # TODO: I forgot some Django urlconf Zen. God will forgive, i won't.

    (r'^groups/(?P<faculty>[^/]+)/(?P<year>[^/]+)',
     'django_schedule.views.list_groups'),

)
