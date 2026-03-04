"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Default to dev locally; production should set DJANGO_SETTINGS_MODULE=config.prod
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.dev')

application = get_asgi_application()
