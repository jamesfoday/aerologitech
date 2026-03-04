from __future__ import annotations

import datetime

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied


def _today_key() -> str:
    today = datetime.date.today().isoformat()
    return f"explore:usage:{today}"


def check_and_increment():
    cap = getattr(settings, "EXPLORE_DAILY_CAP", 500)
    key = _today_key()
    count = cache.get(key, 0)
    if count >= cap:
        raise PermissionDenied("Explore usage cap reached for today.")
    cache.incr(key, 1) if cache.get(key) is not None else cache.set(key, 1, 86400)
    # warn if nearing cap
    if count >= max(int(cap * 0.9), cap - 5):
        print("[Explore] Warning: nearing daily cap", count, "of", cap)
