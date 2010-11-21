from django.conf.urls.defaults import *
from system import views

urlpatterns = patterns('',
    url(r'^job/(?P<job_id>[0-9]+)/result$', views.job_result,
        name='system.job_result'),
    url(r'^start_tests/(?P<name>[a-zA-Z_0-9-]+)$', views.start_tests,
        name='system.start_tests'),
    url(r'^$', views.status, name='system.status'),
)
