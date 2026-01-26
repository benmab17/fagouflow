from .base import *  # noqa
import os
import dj_database_url

DEBUG = False
SECURE_SSL_REDIRECT = False

# Railway utilise DJANGO_SECRET_KEY (pas SECRET_KEY)
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "dev-insecure-secret-key-change-me"
)

# ALLOWED_HOSTS – fallback obligatoire pour éviter le crash
ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
    if h.strip()
]

if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["*"]  # fallback Railway (OK derrière proxy)

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]

# Base de données Railway (Postgres)
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", "sqlite:///db.sqlite3"),
        conn_max_age=600,
        ssl_require=False,
    )
}
