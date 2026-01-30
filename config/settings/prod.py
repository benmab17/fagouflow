from .base import *
import os
import dj_database_url

DEBUG = False

# CORRECTION : Accepte TOUTES les IPs internes de Fly.io
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.fly.dev',
    'fagouflow.fly.dev',
    '.onrender.com',
    '.railway.app',
    '172.19.0.0/16',  # Plage d'IPs internes Fly.io
    '10.0.0.0/8',     # Plage d'IPs privées
]

# Ou plus simple : accepte tout en développement
# ALLOWED_HOSTS = ['*']  # TEMPORAIREMENT pour tester

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

# Security (désactive temporairement pour debug)
SECURE_SSL_REDIRECT = False  # À remettre à True après
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# CSRF
CSRF_TRUSTED_ORIGINS = [
    'https://*.fly.dev',
    'https://*.onrender.com',
    'https://*.railway.app',
]
