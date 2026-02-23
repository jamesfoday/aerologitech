import os
from django.core.wsgi import get_wsgi_application

# Default to prod settings for deployment; override with env if needed
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.prod")
application = get_wsgi_application()
