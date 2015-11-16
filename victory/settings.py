# Django settings for victory project.

import os
# DJANGO_ROOT = os.path.dirname(os.path.realpath(django.__file__))
SITE_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

DEBUG = True

INTERNAL_IPS = ('127.0.0.1', )

# Heroku variable set only for production deploy
if os.environ.get('BOOGIE_PRODUCTION', False):
    DEBUG = False


TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Alper Cugun', ''),
)

MANAGERS = ADMINS

# Databases at the bottom

# Custom settings for logging in
LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'
LOGIN_REDIRECT_URL = '/'


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Amsterdam'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'nl'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(SITE_ROOT, 'sitestatic')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SITE_ROOT, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'boogie.middleware.WWWRedirectMiddleware',
    'boogie.middleware.PreLaunchMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)


TEMPLATE_CONTEXT_PROCESSORS = ("django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages",
    'boogie.context_processors.player'
)



ROOT_URLCONF = 'victory.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'victory.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    
    os.path.join(SITE_ROOT, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'south',
    'boogie',
    'django.contrib.admin',
    'kombu.transport.django',
    'djcelery',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'registration',
    'registration_email',
    'storages',
    'crispy_forms',
    'typogrify'
)

# Setting in django-registration (stupid but can't do anything about that)
ACCOUNT_ACTIVATION_DAYS = 14

AUTHENTICATION_BACKENDS = (
    'registration_email.auth.EmailBackend',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'sake': {
            'handlers': ['console', 'mail_admins'],
            'level': 'INFO',
            'propagate': True
        }
    }
}


import dj_database_url
sqlitepath = 'sqlite:///' + os.path.join(os.path.dirname(SITE_ROOT), 'sake.db')
DATABASES = {
    'default': dj_database_url.config(default=sqlitepath)
}


# E-mail settings
DEFAULT_FROM_EMAIL = ''
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = '587'
EMAIL_HOST_USER = 'hubbub'
EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_PASSWORD', '')


# Celery settings
BROKER_BACKEND = 'django'

CELERY_SEND_TASK_ERROR_EMAILS = True

from datetime import timedelta
CELERYBEAT_SCHEDULE = {
    "new-assignments": {
        "task": "boogie.tasks.pieces_assign",
        "schedule": timedelta(days=1)
    },
    "piece-cleanup": {
        "task": "boogie.tasks.piece_cleanup",
        "schedule": timedelta(hours=1)
    },
    "topic-promote": {
        "task": "boogie.tasks.check_topic_pool",
        "schedule": timedelta(days=1)
    }
}
CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"

import djcelery
djcelery.setup_loader()


# Settings for boto / django-storages

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')
AWS_PRELOAD_METADATA = True
AWS_QUERYSTRING_AUTH = False # Because our images are public

if not DEBUG:
    STATIC_URL = 'https://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
    ADMIN_MEDIA_PREFIX = 'https://%s.s3.amazonaws.com/admin/' % AWS_STORAGE_BUCKET_NAME



CRISPY_TEMPLATE_PACK = 'bootstrap'
