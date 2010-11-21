from django.conf.urls.defaults import *
from work import views

urlpatterns = patterns('',
    url(r'^heartbeat$', views.heartbeat, name='work.heartbeat'),
    url(r'^query$', views.query, name='work.query'),
    url(r'^submit_results$', views.submit_results, 
        name='work.submit_results'),
    url(r'^$', views.work, name='work'),
)
