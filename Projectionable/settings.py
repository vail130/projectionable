import os, sys

# Django settings for Projectionable project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
  ('Vail Gold', 'vail130@gmail.com'),
)

path_components = os.path.dirname(__file__).split('/')
PROJECT_DIR = '/'.join(path_components[:-1]) + '/'

PROJECT_NAME = 'projectionable'
SITE_NAME = 'Projectionable'

MANAGERS = ADMINS

ENVIRONMENT = 'local'

if ENVIRONMENT == 'heroku':
  BASE_URL = 'http://projectionable.herokuapp.com/'
  BIN_PATH = '/app/bin/'
  
  EMAIL_HOST_USER = os.environ['SENDGRID_USERNAME']
  EMAIL_HOST = 'smtp.sendgrid.net'
  EMAIL_PORT = 587
  EMAIL_USE_TLS = True
  EMAIL_HOST_PASSWORD = os.environ['SENDGRID_PASSWORD']
  
  import dj_database_url
  DATABASES = {
    'default': dj_database_url.config(default=os.environ["DATABASE_URL"])
  }
  
elif ENVIRONMENT == 'appfog':
  BASE_URL = 'http://projectionable.aws.us.cm'
  BIN_PATH = '/app/bin/'
  
  import json
  
  ENV_DB_DATA = json.loads(os.getenv("VCAP_SERVICES"))
  CREDENTIALS = ENV_DB_DATA['postgresql-9.1'][0]['credentials']
  
  DATABASES = {
    'default': {
      'ENGINE':   'postgresql_psycopg2',
      'NAME':     CREDENTIALS['name'],
      'USER':     CREDENTIALS['user'],
      'PASSWORD': CREDENTIALS['password'],
      'HOST':     CREDENTIALS['host'],
      'PORT':     CREDENTIALS['port'],
    }
  }
  
else:
  BASE_URL = 'http://127.0.0.1:8000/'
  BIN_PATH = '/usr/local/bin/'
  
  DATABASES = {
    'default': {
      'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
      'NAME': 'app_db',                      # Or path to database file if using sqlite3.
      'USER': 'admin',                      # Not used with sqlite3.
      'PASSWORD': 'p@Rt4yf0R!if3',                  # Not used with sqlite3.
      'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
      'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
  }
  
ADMIN_CODES = {
  "aI05_e`N6=J~W3&ASV9ML3B!72lkR19Ow*(D>LqFAvi8W!39pz|v5Sp[0SCR": "administrator"
}
  
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

TEMPLATE_DIRS = (
  os.path.join(PROJECT_DIR, 'api/templates'),
  os.path.join(PROJECT_DIR, 'client/templates'),
)
  
STATIC_URL = '/static/'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = PROJECT_DIR + 'media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_DIR, 'temp/')

# Additional locations of static files
STATICFILES_DIRS = (
  # Put strings here, like "/home/html/static" or "C:/www/django/static".
  # Always use forward slashes, even on Windows.
  # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
  'django.contrib.staticfiles.finders.FileSystemFinder',
  'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#  'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'jub=9^t7d6!8axdml$#4gwe+fx$5ace!o)vu=nwb4-#fl3ixoc'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
  'django.template.loaders.filesystem.Loader',
  'django.template.loaders.app_directories.Loader',
#  'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
  'django.middleware.common.CommonMiddleware',
  'django.contrib.sessions.middleware.SessionMiddleware',
  'django.middleware.csrf.CsrfViewMiddleware',
  'django.contrib.auth.middleware.AuthenticationMiddleware',
  'django.contrib.messages.middleware.MessageMiddleware',
  # Uncomment the next line for simple clickjacking protection:
  # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'Projectionable.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'Projectionable.wsgi.application'

TEMPLATE_CONTEXT_PROCESSORS = (
  'django.core.context_processors.debug',
  'django.core.context_processors.i18n',
  'django.core.context_processors.media',
  'django.core.context_processors.static',
  'django.contrib.auth.context_processors.auth',
  'django.contrib.messages.context_processors.messages',
)

INSTALLED_APPS = (
  'django.contrib.auth',
  'django.contrib.contenttypes',
  'django.contrib.sessions',
  'django.contrib.sites',
  'django.contrib.messages',
  'django.contrib.staticfiles',
  # Uncomment the next line to enable the admin:
  # 'django.contrib.admin',
  'rest_framework',
  'requests',
  'gunicorn',
  ###########
  'utilities',
  'api',
  'client',
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
    }
  },
  'loggers': {
    'django.request': {
      'handlers': ['mail_admins'],
      'level': 'ERROR',
      'propagate': True,
    },
  }
}
