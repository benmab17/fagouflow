from .base import *  # noqa
import os
import dj_database_url

DEBUG = False
SECURE_SSL_REDIRECT = False
SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-secret-key-change-me")

ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]

CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]


# Railway fournit DATABASE_URL automatiquement quand Postgres est attaché
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", "sqlite:///db.sqlite3"),
        conn_max_age=600,
        ssl_require=False,  # Railway gère TLS côté infra
    )
}
