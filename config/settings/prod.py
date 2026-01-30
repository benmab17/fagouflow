from .base import *

DEBUG = False

# ALLOWED_HOSTS
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.fly.dev',
    'fagouflow.fly.dev',
    '.onrender.com',
    '.railway.app',
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# CSRF - CORRECTION ICI
CSRF_TRUSTED_ORIGINS = [
    'https://fagouflow.fly.dev',
    'https://*.fly.dev',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# Désactive certaines sécurités temporairement pour debug
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# Pour les fichiers statics/media
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
