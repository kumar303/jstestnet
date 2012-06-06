from django.conf import settings
from django.contrib import admin
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^work/', include('jstestnet.work.urls')),
    # Note that /admin is used by system.urls
    (r'^admin-contrib/', include(admin.site.urls)),
)

if settings.DEBUG:
    # Remove leading and trailing slashes so the regex matches.
    media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % media_url, 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )

urlpatterns += patterns('',
    (r'', include('jstestnet.system.urls')),
)
