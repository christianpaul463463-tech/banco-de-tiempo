# Settings exclusivo para GitHub Actions CI
# Hereda todo de settings.py pero sobreescribe la BD con SQLite

import os
os.environ.setdefault("SECRET_KEY", "django-insecure-clave-temporal-para-ci")

from .settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_test.sqlite3",
    }
}
