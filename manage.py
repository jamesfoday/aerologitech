import os
import sys
from dotenv import load_dotenv

def main():
    load_dotenv()
    # Default to local dev settings; deployment overrides via DJANGO_SETTINGS_MODULE=config.prod
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.dev")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
