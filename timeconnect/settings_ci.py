# Settings exclusivo para GitHub Actions CI
# Hereda todo de settings.py pero sobreescribe la BD con SQLite

from .settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_test.sqlite3",
    }
}
