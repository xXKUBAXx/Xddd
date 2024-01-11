"""
Django settings for app project.

Generated by 'django-admin startproject' using Django 4.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-p^ar*%)gw3pne6%k%hxac*k-zh*g#acyk+=n^lxtjg3llh96!f'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['zapleczara.pl', '0.0.0.0', '127.0.0.1', 'localhost', '188.68.247.52'] 

CSRF_TRUSTED_ORIGINS = [
    'http://192.168.100.30', 
    'https://zapleczara.pl'
    ]



SITE_ID=4


# Application definition

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'backend.apps.BackendConfig',
    'rest_framework',
    'drf_yasg',
    'adrf',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'channels'
]

ASGI_APPLICATION = "app.asgi.application"

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": {
            "profile",
            "email"
        },
        "AUTH_PARAMS": {"access_type": "online"}
    }
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'app.urls'

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

WSGI_APPLICATION = 'app.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3' if DEBUG else '/actions-runner/work/django/db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Warsaw'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

import os
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'backend/static')
]
# STATIC_ROOT=os.path.join(BASE_DIR,'staticfiles')
STATIC_ROOT='/actions-runner/work/django/static/'


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

 



AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# Additional configuration settings
SOCIALACCOUNT_LOGIN_ON_GET=True
SOCIALACCOUNT_QUERY_EMAIL = True
ACCOUNT_LOGOUT_ON_GET= True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_REQUIRED = True

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'write-zaplecza': '10/h',
        'structure': '20/h'
    }
}

import os

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    
    'formatters': {
        'full': {
            'format': '[{asctime}] {message}',
            'style': '{',
        },
    },
    
    'filters': {
        'logger_filter': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda record: 'logger' not in record.module,
        },
        'ws_filter': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda record: 'WebSocket' not in record.getMessage(),
        },
        'get_filter': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda record: 'GET' not in record.getMessage(),
        },
        'http_200_filter': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda record: 'HTTP/1.1 200 OK' not in record.getMessage(),
        },
    },
    
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'full',
            'level': 'INFO',
            'filters': [
                'logger_filter', 
                'ws_filter', 
                'get_filter',
                'http_200_filter'
                ],  # Apply the module filter
        },
        'file': {
            'class': 'logging.FileHandler',
            'formatter': 'full',
            'filename': 'info.log',
            'level' : 'INFO',
            'filters' : ['ws_filter'],
        },
    },
    
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },

    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}

