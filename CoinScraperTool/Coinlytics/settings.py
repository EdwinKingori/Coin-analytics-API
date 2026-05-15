import os
from pathlib import Path
from decouple import config
from datetime import timedelta

import core.logging_config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


CELERY_BEAT_SCHEDULE = {
    "clean_old_logs_daily": {
        "task": "core.tasks.clean_old_logs",
        "schedule": timedelta(days=1),
    },
}


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'scraper_app',
    'users',
    'api',
    # ThirdParty Tools
    'rest_framework',
    'rest_framework.authtoken',
    'djoser',
    'django_filters',
    'debug_toolbar',
    'django_extensions',
    # django-celery-beat: stores the periodic task schedule in the database so
    # tasks can be managed via the Django admin panel without restarting Beat.
    'django_celery_beat',
    # django-cors-headers: required for the React frontend (and Postman in
    # non-browser contexts) to make cross-origin requests to the DRF API.
    # Without this, browsers block all API responses from a different origin.
    'corsheaders',
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # CorsMiddleware must come before CommonMiddleware so that CORS response
    # headers are added before Django short-circuits the request on OPTIONS
    # preflight checks. Placing it after CommonMiddleware causes preflight
    # requests to return 200 without CORS headers, breaking browser clients.
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Coinlytics.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates'
        ],
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

WSGI_APPLICATION = 'Coinlytics.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': config('DATABASE_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DATABASE_NAME'),
        'HOST': config('DATABASE_HOST'),
        "PORT": config('DATABASE_PORT'),
        'USER': config('DATABASE_USER'),
        'PASSWORD': config('DATABASE_PASSWORD'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static'
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ✅ Celery Configuration settings
CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/0"
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'


# ✅ Referencing the user model
AUTH_USER_MODEL = 'users.CustomUser'

# ✅ Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_PORT = 587
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')

# ✅ Setting the authenticatication and permission policies
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend']
}
# ✅ Specifying the header type to be used in Postman
SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('Bearer',),
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1)

}

# ✅ Referencing Djoser's serializer to reflect on the auth page
DJOSER = {
    "SERIALIZERS": {
        'user_create': 'users.serializers.UserCreateSerializer',
        'current_user': 'users.serializers.UserSerializer'
    }
}

# ✅ CORS Configuration
# CORS_ALLOWED_ORIGINS lists the exact front-end origins that may call this API
# from a browser. In development the React dev server typically runs on 3000;
# in production replace these with the actual deployed frontend URL.
# Never use CORS_ALLOW_ALL_ORIGINS=True in production — it bypasses the
# same-origin policy for every client, including malicious ones.
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",   # React dev server
    "http://127.0.0.1:3000",
]

# Allow the JWT Authorization header to be sent cross-origin. Without this,
# browsers strip the Authorization header on cross-origin requests and every
# authenticated API call returns 401.
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# ✅ Celery Beat — DatabaseScheduler
# Tells Beat to read its schedule from the django_celery_beat tables rather
# than a static file. This means new periodic tasks can be added through the
# Django admin without restarting the Beat container.
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
