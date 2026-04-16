from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ============= SECURITY SETTINGS =============
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-climate-credit-key-change-in-production')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Render.com deployment - add your domain here
ALLOWED_HOSTS = ['*']  # For development; restrict this in production

CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://render.com',
    'http://localhost:8000',
    'http://localhost:3000',
    'https://yourdomain.com',  # Add your actual Render domain
]

# ============= SESSION & CSRF SETTINGS =============
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
CSRF_COOKIE_HTTPONLY = False  # JavaScript needs to read CSRF token
CSRF_COOKIE_AGE = 31449600  # 1 year - prevent CSRF token expiration
CSRF_USE_SESSIONS = False  # Use cookie-based CSRF tokens

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'climate_credit.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
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

WSGI_APPLICATION = 'climate_credit.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ============= STATIC FILES =============
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'core' / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============= SECURITY & PRODUCTION =============
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
