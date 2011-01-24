
import os
import sys

# Pick up settings_local module in the root directory:
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             '..')))

os.environ["DJANGO_SETTINGS_MODULE"] = "settings_local"
from django.conf import settings

from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
