from django.conf.urls.defaults import *
from system import views

urlpatterns = patterns('',
    url(r'^restart_workers$', views.restart_workers,
        name='system.restart_workers'),
    url(r'^test/(?P<test_run_id>[0-9]+)/result$', views.test_result,
        name='system.test_result'),
    url(r'^start_tests/(?P<name>[a-zA-Z_0-9-]+)$', views.start_tests,
        name='system.start_tests'),
    # Not Django admin
    url(r'^admin/$', views.test_suites, name='system.test_suites'),
    url(r'^admin/test_suite/([^/]+)$', views.test_suites,
        name='system.edit_test_suite'),
    url(r'^admin/create_edit_test_suite/([^/]+)?$',
        views.create_edit_test_suite, name='system.create_edit_test_suite'),
    url(r'^admin/delete_test_suite/([^/]+)$', views.delete_test_suite,
        name='system.delete_test_suite'),
    url(r'^$', views.status, name='system.status'),
)
