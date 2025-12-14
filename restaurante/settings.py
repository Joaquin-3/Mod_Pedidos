"""
Django settings for restaurante project.
Preparado para desarrollo local y despliegue en Render.
"""

from pathlib import Path
import os

# ---------------------------------------------------------------------
# Rutas base
# ---------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------
# Helpers para variables de entorno
# ---------------------------------------------------------------------
def _list_env(name: str, default: str = ""):
    """
    Lee una variable de entorno separada por comas y devuelve una lista.
    Ej: "a.com,b.com" -> ["a.com","b.com"]
    """
    v = os.getenv(name, default)
    return [s.strip() for s in v.split(",") if s.strip()]

def _bool_env(name: str, default: str = "False"):
    return os.getenv(name, default).lower() in {"1", "true", "yes", "on"}

# ---------------------------------------------------------------------
# Seguridad / Entorno
# ---------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")  # cambia en prod
DEBUG = _bool_env("DEBUG", "True")

# Local por defecto; en Render agrega tu dominio en Environment → ALLOWED_HOSTS
ALLOWED_HOSTS = _list_env("ALLOWED_HOSTS", "127.0.0.1,localhost")
CSRF_TRUSTED_ORIGINS = _list_env("CSRF_TRUSTED_ORIGINS", "http://127.0.0.1,http://localhost")

# ---------------------------------------------------------------------
# Integraciones / Flags
# ---------------------------------------------------------------------
USE_MOCKS = _bool_env("USE_MOCKS", "True")  # True para demo
M3_WEBHOOK_SECRET = os.getenv("M3_WEBHOOK_SECRET", "dev-secret")

# Si usas mocks, estas URLs pueden ser locales o el mismo host en cloud
M1_BASE_URL = os.getenv("M1_BASE_URL", "http://127.0.0.1:8000/mock")
M4_BASE_URL = os.getenv("M4_BASE_URL", "http://127.0.0.1:8000/mock")

# ---------------------------------------------------------------------
# Apps
# ---------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'django.contrib.humanize',
    "rest_framework",
    "pedidos",
    "mock",
    "panel",
    "ui",
]

# ---------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # estáticos en prod
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

ROOT_URLCONF = "restaurante.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "restaurante.wsgi.application"

# ---------------------------------------------------------------------
# Base de datos: carpeta escribible dentro del proyecto
# (en Render: /opt/render/project/src/data)
# ---------------------------------------------------------------------
DATA_DIR = BASE_DIR / "data"
os.makedirs(DATA_DIR, exist_ok=True)

SQLITE_PATH = os.getenv("SQLITE_PATH", str(DATA_DIR / "db.sqlite3"))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": SQLITE_PATH,
    }
}

# ---------------------------------------------------------------------
# Password validators
# ---------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------
# Internacionalización
# ---------------------------------------------------------------------
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------
# Archivos estáticos (WhiteNoise)
# ---------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ---------------------------------------------------------------------
# DRF (opcional)
# ---------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

# ---------------------------------------------------------------------
# PK por defecto
# ---------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
