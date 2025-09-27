# config/prod.py
from __future__ import annotations

import os
import dj_database_url

from .base import *  # noqa


# --------------------------------------------------------------------
# FLAGS / SECRETS
# --------------------------------------------------------------------
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
# Allow SECRET_KEY from env to override base
SECRET_KEY = os.getenv("SECRET_KEY", SECRET_KEY)  # type: ignore[name-defined]


# --------------------------------------------------------------------
# HOSTS / CSRF
# --------------------------------------------------------------------
# ALLOWED_HOSTS: comma or space separated
_raw_hosts = os.getenv("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for chunk in _raw_hosts.split(",") for h in chunk.split() if h.strip()]
if not ALLOWED_HOSTS:
    # First deploy convenience; restrict once your domain is set
    ALLOWED_HOSTS = ["*"]

# CSRF_TRUSTED_ORIGINS: comma or space separated; if absent, infer from hosts + Render wildcard
_raw_csrf = os.getenv("CSRF_TRUSTED_ORIGINS", "")
if _raw_csrf.strip():
    CSRF_TRUSTED_ORIGINS = [o.strip() for chunk in _raw_csrf.split(",") for o in chunk.split() if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS if "." in h and not h.startswith(".")]
    if "https://*.onrender.com" not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append("https://*.onrender.com")


# --------------------------------------------------------------------
# DATABASE (Render Postgres w/ SSL)
# --------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/db.sqlite3"),  # type: ignore[name-defined]
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,  # forces ?sslmode=require for Postgres
    )
}


# --------------------------------------------------------------------
# STATIC via WhiteNoise  |  MEDIA via Cloudinary (if enabled)
# --------------------------------------------------------------------
# Ensure WhiteNoise middleware is present right after SecurityMiddleware
if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    # SecurityMiddleware is typically index 0
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

USE_CLOUDINARY = bool(os.getenv("CLOUDINARY_URL"))

# Ensure cloudinary apps are present and ordered (cloudinary_storage BEFORE staticfiles)
if USE_CLOUDINARY:
    # Avoid duplicates if defined in base
    for app in ("cloudinary_storage", "cloudinary"):
        if app in INSTALLED_APPS:
            INSTALLED_APPS.remove(app)

    if "django.contrib.staticfiles" in INSTALLED_APPS:
        idx = INSTALLED_APPS.index("django.contrib.staticfiles")
        INSTALLED_APPS.insert(idx, "cloudinary_storage")
        INSTALLED_APPS.insert(idx + 1, "cloudinary")
    else:
        INSTALLED_APPS += ["cloudinary_storage", "cloudinary"]

# Use STORAGES (Django 4.2+) so defaults are explicit
if USE_CLOUDINARY:
    STORAGES = {
        "default": {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
    CLOUDINARY_STORAGE = {
        "SECURE": True,  # force https URLs
        # You can add folders/transforms here if needed
        # e.g. "PREFIX": "aerologitech",
    }
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }

# --- Legacy aliases for packages expecting old names (needed by django-cloudinary-storage) ---
STATICFILES_STORAGE = STORAGES["staticfiles"]["BACKEND"]
if USE_CLOUDINARY:
    DEFAULT_FILE_STORAGE = STORAGES["default"]["BACKEND"]

# Manifest strictness (True recommended). Set WHITENOISE_MANIFEST_STRICT=false to avoid 500s during dev.
WHITENOISE_MANIFEST_STRICT = os.getenv("WHITENOISE_MANIFEST_STRICT", "true").lower() == "true"

# Harmless with Cloudinary; helpful if falling back locally
MEDIA_URL = "/media/"


# --------------------------------------------------------------------
# SECURITY (behind Render proxy)
# --------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "true").lower() == "true"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Enable HSTS once HTTPS is fully working end-to-end
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True


# --------------------------------------------------------------------
# EMAIL (optional, from env)
# --------------------------------------------------------------------
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", EMAIL_BACKEND)  # type: ignore[name-defined]
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587")) if EMAIL_HOST else 587
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"


# --------------------------------------------------------------------
# LOGGING (errors to console → visible in Render logs)
# --------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}
