import os
from django.core.wsgi import get_wsgi_application

# Default to dev for local runserver; production should set DJANGO_SETTINGS_MODULE=config.prod
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.dev")
application = get_wsgi_application()
