"""
Django settings for llab web project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import mimetypes

mimetypes.init()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# The path where Dulwich / git-protocol will clone the repositories
GIT_REPOSITORY_PATH = os.path.join(BASE_DIR, 'repositories')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY_PRODUCTION = None
if DEBUG:
    SECRET_KEY = '^9uhjoh&dd=k!w4eblmbgykai@s&-b7@gmf7(y9)!c-9yzkun5'
elif not SECRET_KEY_PRODUCTION:
    raise Exception('SECRET_KEY_PRODUCTION is not set. Keep this a secret!')
else:
    SECRET_KEY = SECRET_KEY_PRODUCTION


#SSH_KEY_MANAGEMENT_BACKEND =  'llab.auth.openssh_database_backend'
SSH_KEY_MANAGEMENT_BACKEND = 'llab.auth.openssh_copyid_backend'

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = (
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Project apps
    'account',
    'account.settings',
    'organization',
    'project',
    'web',

    # Local builtins
    'account.user_streams_single_table_backend',

    # Third party
    'django_gravatar',
    'bootstrap3',
    'user_streams',
    'json_field',

    # Django contribs
    'django.contrib.humanize'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'web.urls'

USER_STREAMS_BACKEND = ('account.'
                        'user_streams_single_table_backend.'
                        'SingleTableDatabaseBackend')

WSGI_APPLICATION = 'web.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
AUTH_USER_MODEL = 'account.User'
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/account/login/'
LOGOUT_URL = '/account/logout/'
