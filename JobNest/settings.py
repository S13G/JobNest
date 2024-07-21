"""
Django settings for JobNest project.
"""
import os
from datetime import timedelta
from pathlib import Path

from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
DJANGO_APPS = [
    "daphne",
    "jazzmin",  # not a django app but a custom django admin library
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

LOCAL_APPS = [
    'apps.core.apps.CoreConfig',
    'apps.common.apps.CommonConfig',
    'apps.jobs.apps.JobsConfig',
    'apps.misc.apps.MiscConfig',
    'apps.social_auth.apps.SocialAuthConfig',
    'apps.chat.apps.ChatConfig',
    'apps.notification.apps.NotificationConfig',
]

THIRD_PARTY_APPS = [
    "channels",
    "cloudinary_storage",
    "debug_toolbar",
    "django_filters",
    "drf_spectacular",
    "rest_framework",
    "rest_framework.authtoken",  # for testing purposes
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "treblle",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'treblle.middleware.TreblleMiddleware',
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "COERCE_DECIMAL_TO_STRING": False,
    "DEFAULT_PAGINATION_CLASS": "apps.common.paginator.CustomPagination",
    "EXCEPTION_HANDLER": "apps.common.exceptions.custom_exception_handler",
    "PAGE_SIZE": 30,
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "1000/day", "user": "2500/day"},
    "NON_FIELD_ERRORS_KEY": "error",
}

CORS_ALLOW_HEADERS = (
    "accept",
    "accept-language",
    "access-control-request-headers",
    "access-control-request-method",
    "authorization",
    "content-disposition",
    "content-encoding",
    "content-length",
    "content-type",
    "cookie",
    "host",
    "origin",
    "referer",
    "user-agent",
    "x-forwarded-for",
    "x-requested-with",
)

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True

SPECTACULAR_SETTINGS = {
    "TITLE": "JOBNEST API",
    "DESCRIPTION": """
    🚀 JobNest: Your Dream Job is Just a Click Away 
    Welcome to JobNest, the future of job hunting. We're here to connect students with their dream jobs. With features like registration, job application, CV submission, and more, we're making the job hunting process easy and efficient. Join us today and kickstart your career journey! 🌟👩‍🎓👨‍
    """,
    "VERSION": "1.0.0",
    "CONTACT": "ayflix0@gmail.com",
    "SCHEMA_PATH_PREFIX": r'/api/v[0-9]',
    "SERVE_INCLUDE_SCHEMA": False,
    "DISABLE_ERRORS_AND_WARNINGS": True,
}

INTERNAL_IPS = [
    "127.0.0.1",
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "KEY_PREFIX": "jobnest",
    }
}

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ACCESS_TOKEN_LIFETIME": timedelta(days=5),
}

AUTH_USER_MODEL = "core.User"

ROOT_URLCONF = 'JobNest.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'JobNest.wsgi.application'

ASGI_APPLICATION = "JobNest.asgi.application"

# CHANNEL LAYERS
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
#
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('POSTGRES_NAME'),
#         'USER': config('POSTGRES_USER'),
#         'PASSWORD': config('POSTGRES_PASSWORD'),
#         'HOST': config('POSTGRES_HOST'),
#         'PORT': config('POSTGRES_PORT')
#     }
# }

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"

STATICFILES_DIRS = [BASE_DIR / "static"]

STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"

MEDIA_ROOT = BASE_DIR / "static/media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Email settings for SSL(Mainly for development and websocket_test)
EMAIL_USE_TLS = False

EMAIL_USE_SSL = True

EMAIL_HOST = "smtp.gmail.com"

EMAIL_HOST_USER = config("EMAIL_HOST_USER")

EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")

EMAIL_PORT = 465

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

JAZZMIN_SETTINGS = {
    "site_brand": "JobNest ADMIN",
    # title of the window (Will default to current_admin_site.site_title if absent or None)
    "site_title": "JobNest ADMIN",
    # Title on the login screen (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_header": "JobNest",
    # Logo to use for your site, must be present in static files, used for brand on top left
    "site_logo": "../static/logo.png",
    # Logo to use for your site, must be present in static files, used for login form logo (defaults to site_logo)
    "login_logo": "../static/logo.png",
    # CSS classes that are applied to the logo above
    "site_logo_classes": "img-circle",
    # Relative path to a favicon for your site, will default to site_logo if absent (ideally 32x32 px)
    "site_icon": "../static/logo.png",
    # Welcome text on the login screen
    "welcome_sign": "Welcome to the JobNest Admin Section",
    # Copyright on the footer
    "copyright": "JobNest Ltd 2023",
    # The model admin to search from the search bar, search bar omitted if excluded
    "search_model": [],
    # Field name on user model that contains avatar ImageField/URLField/Charfield or a callable that receives the user
    # "user_avatar": "avatar",

    #############
    # User Menu #
    #############
    # Additional links to include in the user menu on the top right ("app" url type is not allowed)
    "usermenu_links": [{"name": "jobnest Platform"}, {"model": "auth.user"}],

    #############
    # Side Menu #
    #############
    # Whether to display the side menu
    "show_sidebar": True,
    # Whether to aut expand the menu
    "navigation_expanded": True,
    # Hide these apps when generating side menu e.g (auth)
    "hide_apps": {"authtoken": ['tokenproxy'], "token_blacklist": ["blacklistedtoken", "outstandingtoken"]},
    # List of apps (and/or models) to base side menu ordering off of (does not need to contain all apps/models)
    "order_with_respect_to": ["auth", "core", "core.user"],

    "icons": {
        "core.group": "fas fa-users",
        "core.user": "fas fa-universal-access",
        "core.profile": "fas fa-user",
        "core.companyprofile": "fas fa-building",
        "core.employeeprofile": "far fa-user",
        "misc.tip": "fas fa-lightbulb",
        "misc.faq": "fas fa-question",
        "misc.faqtype": "fas fa-list",
        "jobs.jobtype": "fas fa-list",
        "jobs.job": "fas fa-briefcase",
        "jobs.appliedjob": "far fa-file",
    },
    # Icons that are used when one is not manually specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    #############
    # UI Tweaks #
    #############
    # "show_ui_builder": True,
    "changeform_format": "horizontal_tabs",
    # override change forms on a per modeladmin basis
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
    },
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-info",
    "accent": "accent-navy",
    "navbar": "navbar-cyan navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": True,
    "sidebar_fixed": True,
    "sidebar": "sidebar-light-info",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "minty",
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-outline-success"
    }
}

SILENCED_SYSTEM_CHECKS = [
    'staticfiles.W004',
]

# database active connection minutes
CONN_MAX_AGE = 300

# Treblle variables
TREBLLE_INFO = {
    'api_key': config('TREBLLE_API_KEY'),
    'project_id': config('TREBLLE_PROJECT_ID')
}
