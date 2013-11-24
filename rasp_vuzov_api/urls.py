from django.conf.urls.defaults import *

urlpatterns = patterns('',

    (r'^$', 'rasp_vuzov_api.views.index'),
    (r'^get_faculties$', 'rasp_vuzov_api.views.get_faculties'),
    (r'^get_groups$', 'rasp_vuzov_api.views.get_groups'),
    (r'^get_schedule$', 'rasp_vuzov_api.views.get_schedule')

)
