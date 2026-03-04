from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.cache import cache

from apps.explore.services.usage_limiter import _today_key


class Command(BaseCommand):
    help = "Show and reset Explore daily usage counters; prints recommended safeguards."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Reset today's counter to 0")

    def handle(self, *args, **options):
        cap = getattr(settings, "EXPLORE_DAILY_CAP", 500)
        key = _today_key()
        current = cache.get(key, 0)

        if options["reset"]:
            cache.set(key, 0, 86400)
            current = 0
            self.stdout.write(self.style.SUCCESS("Counter reset to 0 for today."))

        self.stdout.write(f"Daily cap: {cap}")
        self.stdout.write(f"Current count: {current}")
        self.stdout.write("Recommended: set GOOGLE_MAPS_API_KEY env; monitor billing via Google Cloud console; adjust EXPLORE_DAILY_CAP if needed.")
