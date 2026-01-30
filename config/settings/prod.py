from .base import *

DEBUG = False
ALLOWED_HOSTS = ['*']  # ACCEPTE TOUT

# Database SQLite (simple)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Désactive CSRF temporairement
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# Pas de CSRF_TRUSTED_ORIGINS pour l'instant
