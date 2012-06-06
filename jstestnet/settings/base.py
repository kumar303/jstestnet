# This is your project's main settings file that can be committed to your
# repo. If you need to override a setting locally, use settings_local.py

from funfactory.settings_base import *
from funfactory.utils import get_middleware, get_apps

# Name of the top-level module where you put all your apps.
# If you did not install Playdoh with the funfactory installer script
# you may need to edit this value. See the docs about installing from a
# clone.
PROJECT_MODULE = 'jstestnet'

# Bundles is a dictionary of two dictionaries, css and js, which list css files
# and js files that can be bundled together by the minify app.
MINIFY_BUNDLES = {
    'css': {
        'common': (
            'css/minimalist/style.css',
            'css/style.css',
        ),
    },
    'js': {
        'common': (
            'js/libs/jquery.js',
            'js/libs/json2.js',
            'js/libs/socket.io.js',
        ),
        'system': (
            'js/system.js',
        ),
        'work': (
            'js/work.js',
        ),
    }
}

# Defines the views served for root URLs.
ROOT_URLCONF = '%s.urls' % PROJECT_MODULE

INSTALLED_APPS = list(get_apps([])) + [
    'django.contrib.admin',

    # Application base, containing global templates.
    'jstestnet.base',

    # Local apps
    'jstestnet.system',
    'jstestnet.work',
]

MIDDLEWARE_CLASSES = get_middleware([
    'funfactory.middleware.LocaleURLMiddleware',
])


# Because Jinja2 is the default template loader, add any non-Jinja templated
# apps here:
JINGO_EXCLUDE_APPS = [
    'admin',
    'registration',
]

# Tells the extract script what files to look for L10n in and what function
# handles the extraction. The Tower library expects this.
DOMAIN_METHODS['messages'] = [
    ('%s/**.py' % PROJECT_MODULE,
        'tower.management.commands.extract.extract_tower_python'),
    ('%s/**/templates/**.html' % PROJECT_MODULE,
        'tower.management.commands.extract.extract_tower_template'),
    ('templates/**.html',
        'tower.management.commands.extract.extract_tower_template'),
],

# paths that don't require a locale prefix
# NOTE: locale middleware has been disabled.
#SUPPORTED_NONLOCALES = (
#    'img',
#    'media',
#    'robots.txt',
#    'system',
#    'work',
#    'admin-contrib',
#)

# # Use this if you have localizable HTML files:
# DOMAIN_METHODS['lhtml'] = [
#    ('**/templates/**.lhtml',
#        'tower.management.commands.extract.extract_tower_template'),
# ]

# # Use this if you have localizable JS files:
# DOMAIN_METHODS['javascript'] = [
#    # Make sure that this won't pull in strings from external libraries you
#    # may use.
#    ('media/js/**.js', 'javascript'),
# ]


# For bcrypt only:
HMAC_KEYS = {
    #'2012-06-01': 'Example of shared key',
}

# Use sha 256 by default but support any other algorithm:
BASE_PASSWORD_HASHERS = (
    'django_sha2.hashers.SHA256PasswordHasher',
    'django_sha2.hashers.BcryptHMACCombinedPasswordVerifier',
    'django_sha2.hashers.SHA512PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
)

from django_sha2 import get_password_hashers
PASSWORD_HASHERS = get_password_hashers(BASE_PASSWORD_HASHERS, HMAC_KEYS)

LOGGING = dict(loggers=dict(playdoh = {'level': logging.DEBUG},
                            jstestnet = {'level': logging.INFO}))

# When True, always provide CSRF protection for anonymous users.
# This is required to get admin logins to work w/ django-session-csrf.
ANON_ALWAYS = True
