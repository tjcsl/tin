"""Django settings for tin project.

Generated by 'django-admin startproject' using Django 2.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from __future__ import annotations

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEDIA_ROOT = os.path.join(BASE_DIR, "media")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "naxigo(w3=$1&!-t4vbb9)g^8#lnt6ygr)(2qfi1z(h(r_cjhy"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "tin",
    "tin.tjhsst.edu",
    "tin.csl.tjhsst.edu",
    "tin.sites.tjhsst.edu",
]

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]


# Application definition

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "social_django",
    "django_extensions",
    "django_celery_results",
    "debug_toolbar",
    "markdownify.apps.MarkdownifyConfig",
    "tin.apps",
    "tin.apps.users",
    "tin.apps.auth",
    "tin.apps.courses",
    "tin.apps.assignments",
    "tin.apps.submissions",
    "tin.apps.docs",
    "tin.apps.venvs",
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tin.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
                "tin.apps.context_processors.response_footer",
            ]
        },
    }
]

WSGI_APPLICATION = "tin.wsgi.application"
ASGI_APPLICATION = "tin.asgi.application"


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [("localhost", 6379)]},
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TEST_RUNNER = "tin.tests.runner.PytestRunner"


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

if DEBUG:
    AUTH_PASSWORD_VALIDATORS = []
else:
    AUTH_PASSWORD_VALIDATORS = [
        {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
        {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
        {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]


# Authentication-related settings

AUTHENTICATION_BACKENDS = ("tin.apps.auth.oauth.IonOauth2",)

if DEBUG:
    AUTHENTICATION_BACKENDS += ("django.contrib.auth.backends.ModelBackend",)

SOCIAL_AUTH_USER_FIELDS = [
    "username",
    "full_name",
    "first_name",
    "last_name",
    "email",
    "id",
    "is_student",
    "is_teacher",
]

SOCIAL_AUTH_URL_NAMESPACE = "social"

SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "tin.apps.auth.oauth.get_username",
    "social_core.pipeline.social_auth.associate_by_email",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
)

AUTH_USER_MODEL = "users.User"

SOCIAL_AUTH_ALWAYS_ASSOCIATE = True

LOGOUT_URL = "/logout/"

LOGIN_URL = "/login/"

LOGIN_REDIRECT_URL = "/"

SOCIAL_AUTH_LOGIN_ERROR_URL = "/"
SOCIAL_AUTH_RAISE_EXCEPTIONS = False


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/New_York"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = "/static/"

STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)
STATIC_ROOT = os.path.join(BASE_DIR, "serve")


# Logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "{asctime}: {levelname:>8s}: {message}", "style": "{"}},
    "handlers": {
        "console": {"level": "DEBUG", "class": "logging.StreamHandler", "formatter": "simple"},
        "info_log": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs/info.log"),
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {"handlers": ["console", "info_log"], "level": "INFO", "propagate": True},
        "tin": {"handlers": ["console", "info_log"], "level": "INFO", "propagate": True},
    },
}


# Celery settings

CELERY_RESULT_BACKEND = "django-db"


CELERY_BROKER_URL = "redis://localhost:6379/1"


# Markdown
MARKDOWNIFY = {
    "default": {
        "MARKDOWN_EXTENSIONS": [
            "fenced_code",
        ],
        "WHITELIST_ATTRS": ["class", "href", "src", "alt"],
        "WHITELIST_TAGS": [
            "a",
            "abbr",
            "acronym",
            "b",
            "blockquote",
            "code",
            "em",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "i",
            "img",
            "li",
            "ol",
            "p",
            "pre",
            "span",
            "strong",
            "ul",
        ],
    }
}


# Django debug toolbar settings

_enabled_panels = {
    "debug_toolbar.panels.history.HistoryPanel",
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    "debug_toolbar.panels.profiling.ProfilingPanel",
}

DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": _enabled_panels,
    "SHOW_COLLAPSED": True,
}

# Tin-specific settings

SUBMISSION_SIZE_LIMIT = 1 * 1000 * 1000  # 1 MB

DEVELOPER_EMAIL = "tin@tjhsst.edu"
REPO_URL = "https://github.com/tjcsl/tin"

VENV_FILE_SIZE_LIMIT = 1 * 1000 * 1000 * 1000  # 1 GB

# Spaces and special characters may not be handled correctly
# Not importing correctly - specified directly in apps/submissions/tasks.py
# as of 8/3/2022, 2022ldelwich
SUBMISSION_PYTHON = "/usr/bin/python3.10"

SUBMISSION_NAMESERVERS = ["198.38.16.40", "198.38.16.41"]

# Users may only have this many submissions running
CONCURRENT_USER_SUBMISSION_LIMIT = 2

# Threshold for log messages being issues
QUIZ_ISSUE_THRESHOLD = 5

# ImgBB API key (set in secret.py)
IMGBB_API_KEY = ""

try:
    from .secret import *
except ImportError:
    pass
