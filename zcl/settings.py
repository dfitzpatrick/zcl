"""
ZONE CONTROL LEAGUES
Written by Derek Fitzpatrick
dfitz.murrieta@gmail.com
February, 2020

"""

import os
import socket
from decouple import config

"""
BASE SETTINGS
-------------------------------------------------------------------------------
"""
ENABLE_TOOLBAR = False
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', cast=bool, default=False)
SECURE_SSL_REDIRECT = False
ALLOWED_HOSTS = ['*']
AUTH_USER_MODEL = 'accounts.DiscordUser'
ROOT_URLCONF = 'zcl.urls'
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = True
ASGI_APPLICATION = "zcl.routing.application"
WSGI_APPLICATION = 'zcl.wsgi.application'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


"""
DATASTORE AND TASKS
-------------------------------------------------------------------------------
"""
REDIS_URL = config('REDIS_URL', default='redis://redis:6379/0')
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_ACCEPT_CONTENT = ['json', 'application/x-python-serialize']
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[:-1] + '1' for ip in ips] + ['127.0.0.1', '10.0.2.2']
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [REDIS_URL],
        },
    },
}
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'zclpassword',
        'HOST': 'db' or 'localhost',
        'PORT': 5432
    }
}

"""
URL PATH SETTINGS
-------------------------------------------------------------------------------
"""
SITE_ID = 1
STATIC_ROOT = '/static/'
STATIC_URL = '/static/'


STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'frontend', "build", "static"),
)
SITE_URL = config('SITE_URL')
PUBLIC_SITE_URL = config('PUBLIC_SITE_URL')

FRONTEND = "http://localhost:8000/"

CORS_ORIGIN_ALLOW_ALL = True
CSRF_TRUSTED_ORIGINS = ['localhost:3000']
CORS_ORIGIN_WHITELIST = (
    'http://localhost:3000',
    'https://localhost:3000',
)

"""
AMAZON WEB SERVICES
-------------------------------------------------------------------------------
"""
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = 'zcleagues'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

"""
AUTHENTICATION AND KEYS
-------------------------------------------------------------------------------
"""
TWITCH_CLIENT_ID = config('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = config('TWITCH_CLIENT_SECRET')

DISCORD_CLIENT_ID = config('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = config('DISCORD_CLIENT_SECRET')

OAUTH2_DISCORD = {
    'authorization_url': 'https://discordapp.com/api/oauth2/authorize',
    'token_url': 'https://discordapp.com/api/v7/oauth2/token',
    'api_url': 'https://discordapp.com/api/v6',
    'client_id': DISCORD_CLIENT_ID,
    'secret': DISCORD_CLIENT_SECRET,
    'redirect_uri': os.path.normpath('{0}/accounts/login'.format(SITE_URL)),
    'scope': 'identify email',

}
OAUTH2_TWITCH = {
    'authorization_url': 'https://id.twitch.tv/oauth2/authorize',
    'token_url': 'https://id.twitch.tv/oauth2/token',
    'client_id': TWITCH_CLIENT_ID,
    'secret': TWITCH_CLIENT_SECRET,
    'scope': 'clips:edit+user:edit',
    'redirect_uri': os.path.normpath('{0}/accounts/twitch/connect'.format(SITE_URL)),
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ]
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)
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


"""
DJANGO APPLICATIONS
-------------------------------------------------------------------------------
"""

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'accounts',
    'sslserver',
    'api',
    'channels',
    'websub',
    'django_filters',


]
if ENABLE_TOOLBAR:
    INSTALLED_APPS += ['debug_toolbar']

"""
LOGGING
-------------------------------------------------------------------------------
"""

LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': "%(asctime)s: | %(name)30s | %(funcName)25s | %(levelname)8s | %(message)s",
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },

    },
    'loggers': {
        'zcl': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },

        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.utils.autoreload': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'websub': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        }

    }
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'zcl.middleware.DisableCSRFMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
if ENABLE_TOOLBAR:
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'frontend'), os.path.join(BASE_DIR, 'templates')]
        ,
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




