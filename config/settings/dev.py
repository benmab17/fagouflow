import os
from .base import *  # noqa
from pathlib import Path

DEBUG = True

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=bool(os.getenv("DATABASE_URL")),
    }
}

DEBUG = True

# --- MEDIA (CLOUDINARY) ---
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.environ.get("CLOUDINARY_CLOUD_NAME", "demo"),
    "API_KEY": os.environ.get("CLOUDINARY_API_KEY", ""),
    "API_SECRET": os.environ.get("CLOUDINARY_API_SECRET", ""),
}
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
