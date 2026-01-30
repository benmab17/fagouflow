from .base import *
import os
import dj_database_url

DEBUG = False

# CORRECTION ICI :
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.fly.dev',           # Pour tous les sous-domaines Fly.io
    'fagouflow.fly.dev',  # Ton domaine exact
    '.onrender.com',
    '.railway.app',
]

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3'),
        conn_max_age=600
    )
}

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# CSRF
CSRF_TRUSTED_ORIGINS = [
    'https://*.fly.dev',
    'https://*.onrender.com',
    'https://*.railway.app',
]
