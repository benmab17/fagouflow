from .base import *  # noqa
import os
import dj_database_url

# --- Core ---
DEBUG = False

# Railway est derrière un proxy TLS (HTTPS)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = False  # tu peux mettre True plus tard quand tout est stable

# Railway utilise DJANGO_SECRET_KEY (pas SECRET_KEY)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-secret-key-change-me")

# --- Hosts / CSRF ---
ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
    if h.strip()
]

# Fallback pour éviter un crash si variable vide
# (Tu peux retirer "*" une fois que tu es sûr de tes domaines)
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]

# --- Database (Railway Postgres) ---
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", "sqlite:///db.sqlite3"),
        conn_max_age=600,
        ssl_require=False,
    )
}

# --- Cookies / Sessions (important en HTTPS) ---
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"

# --- Auth redirects ---
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/login/"
