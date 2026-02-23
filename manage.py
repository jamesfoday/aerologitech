import os
import sys

def main():
    # Default to production settings; override locally with DJANGO_SETTINGS_MODULE=config.dev
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.prod")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
