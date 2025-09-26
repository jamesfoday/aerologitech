# config/prod.py
from __future__ import annotations

import os
import dj_database_url

from .base import *  # noqa

# --------------------------------------------------------------------
# FLAGS / SECRETS
# --------------------------------------------------------------------
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
# If your base file defines SECRET_KEY already, the env value will override it:
SECRET_KEY = os.getenv("SECRET_KEY", SECRET_KEY)  # type: ignore[name-defined]

# --------------------------------------------------------------------
# HOSTS / CSRF
# --------------------------------------------------------------------
# ALLOWED_HOSTS: comma or space separated
_raw_hosts = os.getenv("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for chunk in _raw_hosts.split(",") for h in chunk.split() if h.strip()]

# If you prefer an easier first deploy, leave this open when nothing provided.
# (Tighten to explicit domains as soon as you're live.)
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["*"]

# CSRF_TRUSTED_ORIGINS: allow comma or space separated values; if not provided,
# derive from ALLOWED_HOSTS and add the Render wildcard as a convenience.
_raw_csrf = os.getenv("CSRF_TRUSTED_ORIGINS", "")
if _raw_csrf.strip():
    CSRF_TRUSTED_ORIGINS = [
        o.strip()
        for chunk in _raw_csrf.split(",")
        for o in chunk.split()
        if o.strip()
    ]
else:
    CSRF_TRUSTED_ORIGINS = [
        f"https://{h}"
        for h in ALLOWED_HOSTS
        if "." in h and not h.startswith(".")
    ]
    # Helpful default for Render
    if "https://*.onrender.com" not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append("https://*.onrender.com")

# --------------------------------------------------------------------
# DATABASE (Render Postgres needs SSL)
# --------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/db.sqlite3"),
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,  
    )
}

# --------------------------------------------------------------------
# STATIC via WhiteNoise
# --------------------------------------------------------------------
# Ensure WhiteNoise is present right after SecurityMiddleware
if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# --------------------------------------------------------------------
# SECURITY (behind Render's proxy)
# --------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "true").lower() == "true"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Set HSTS after you confirm HTTPS is working end-to-end
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# --------------------------------------------------------------------
# EMAIL (optional, from env)
# --------------------------------------------------------------------
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", EMAIL_BACKEND)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587")) if EMAIL_HOST else 587
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"

# --------------------------------------------------------------------
# OPTIONAL: Cloudinary media
# --------------------------------------------------------------------
if os.getenv("CLOUDINARY_URL"):
    INSTALLED_APPS += ["cloudinary", "cloudinary_storage"]
    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

# --------------------------------------------------------------------
# LOGGING (send errors to console so they appear in Render logs)
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
