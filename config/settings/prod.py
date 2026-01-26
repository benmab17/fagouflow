import os
import dj_database_url
from .base import * # noqa

# --- SÉCURITÉ CORE ---
DEBUG = False
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

# --- HOSTS & CSRF ---
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "fagouflow.onrender.com").split(",")
    if h.strip()
]

CSRF_TRUSTED_ORIGINS = [
    f"https://{h}" for h in ALLOWED_HOSTS
]

# --- DATABASE ---
DATABASE_URL = os.environ.get("DATABASE_URL")

DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )
}
DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}

# --- SÉCURITÉ HTTPS ---
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"

# --- FICHIERS STATIQUES ---
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"

# --- STOCKAGE (MEDIA & STATIC) ---
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.environ.get("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": os.environ.get("CLOUDINARY_API_KEY"),
    "API_SECRET": os.environ.get("CLOUDINARY_API_SECRET"),
}

# Configuration STORAGES (Corrigée pour éviter l'erreur 500)
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage", # Manifest supprimé ici
    },
}

# Insertion des apps nécessaires
if "cloudinary_storage" not in INSTALLED_APPS:
    INSTALLED_APPS.insert(0, "cloudinary_storage")
if "cloudinary" not in INSTALLED_APPS:
    INSTALLED_APPS.append("cloudinary")
if "whitenoise.runserver_nostatic" not in INSTALLED_APPS:
    INSTALLED_APPS.insert(0, "whitenoise.runserver_nostatic")

MEDIA_URL = "/media/"

# --- LOGGING ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}