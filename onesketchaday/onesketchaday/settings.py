"""
Django settings for onesketchaday project.

Generated by 'django-admin startproject' using Django 4.0.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
with open("./django-token", "r+") as f:
    SECRET_KEY = str(f.readline()).strip()

# SECURITY WARNING: don't run with debug turned on in production!
if os.environ.get('DEBUG') is not None:
    if os.environ['DEBUG'] == "True":
        DEBUG = True
    else:
        DEBUG = False

else:
    DEBUG = False

if os.environ.get('DOMAIN') is not None:
    ALLOWED_HOSTS = [os.environ['DOMAIN']]
else:
    ALLOWED_HOSTS = ['127.0.0.1']

# Application definition

INSTALLED_APPS = [
    'app.apps.AppConfig',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]
AUTH_USER_MODEL = 'app.User'

MIDDLEWARE = [
    'django.middleware.cache.UpdateCacheMiddleware',
    
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'django.middleware.cache.FetchFromCacheMiddleware',
]

ROOT_URLCONF = 'onesketchaday.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'onesketchaday.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

if os.environ.get('DB_HOST') is not None:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'CONN_MAX_AGE' : 3600,

            'NAME': os.environ['DB_NAME'],
            'USER': os.environ['DB_USER'],
            'PASSWORD': os.environ['DB_PASSWORD'],
            'HOST': os.environ['DB_HOST'],
            'PORT': os.environ['DB_PORT'],
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

if not DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'onesketchaday-cache',
            'TIMEOUT': 60,
            'OPTIONS': {
                'MAX_ENTRIES': 1000
            }
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

if os.environ.get('TIME_ZONE') is not None:
    TIME_ZONE = os.environ['TIME_ZONE']
else:
    TIME_ZONE="America/New_York"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

if not os.path.exists(MEDIA_ROOT):
    os.mkdir(MEDIA_ROOT)

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

with open("./discord-token", "r+") as f:
    DISCORD_API_TOKEN = str(f.readline()).strip()

if os.environ.get('SITE_URL') is not None:
    SITE_URL = os.environ['SITE_URL']
else:
    SITE_URL = "http://127.0.0.1:8000"

if os.environ.get('ADMIN_PAGE') is not None:
    ADMIN_PAGE = os.environ['ADMIN_PAGE']
else:
    ADMIN_PAGE = "admin"

DEFAULT_VARIABLES = ["StartDate", "PageIcon", "ReminderMessage", "PostCountMessage", "PostsPerPage"]