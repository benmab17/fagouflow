from .base import *  # noqa
from pathlib import Path

DEBUG = True

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DEBUG = True
