import os
import sys
sys.path.append(os.getcwd())  # add project root, to import settings_local

# For database migrations
import settings_local as settings

db = "mysql --silent -u %s -p'%s' -D %s" % (
                                settings.DATABASES['default']['USER'],
                                settings.DATABASES['default']['PASSWORD'],
                                settings.DATABASES['default']['NAME'])
table = 'schema_version'
