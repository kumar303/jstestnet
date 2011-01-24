
import os
import sys

from os.path import abspath, dirname, join

os.environ["DJANGO_SETTINGS_MODULE"] = "settings_local"
from django.conf import settings

from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
