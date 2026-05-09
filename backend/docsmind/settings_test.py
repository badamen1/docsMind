"""
Configuración de Django para pruebas locales (sin Docker/PostgreSQL).

Uso:
    python manage.py test --settings=docsmind.settings_test <app>

Anula la base de datos a SQLite en memoria para que las pruebas
corran sin necesitar el contenedor de PostgreSQL.
"""

from .settings import *  # noqa: F401, F403

# Usar SQLite en memoria durante los tests locales
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Desactivar advertencias de migración en tests
MIGRATION_MODULES: dict = {}

# Silenciar logs innecesarios durante tests
LOGGING: dict = {}

# Deshabilitar caché en tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}
