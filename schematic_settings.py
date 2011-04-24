# For database migrations
import settings_local as settings

db = "mysql --silent -u %s -p'%s' -D %s" % (
                                settings.DATABASES['default']['USER'],
                                settings.DATABASES['default']['PASSWORD'],
                                settings.DATABASES['default']['NAME'])
table = 'schema_version'
