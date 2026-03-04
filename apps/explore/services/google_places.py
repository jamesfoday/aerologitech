from __future__ import annotations

import hashlib
import json
from typing import Iterable, List, Dict, Any

import requests
from django.conf import settings
from django.core.cache import cache


BASE_URL = "https://places.googleapis.com/v1"


def _cache_key(prefix: str, payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True)
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return f"explore:{prefix}:{digest}"


def nearby_search(
    lat: float,
    lng: float,
    radius_m: int,
    included_types: Iterable[str],
    max_results: int | None = None,
) -> List[Dict[str, Any]]:
    desired = max_results or getattr(settings, "EXPLORE_MAX_RESULTS", 10)
    per_page = min(20, desired)  # API limit per page
    ttl = getattr(settings, "EXPLORE_CACHE_TTL_NEARBY", 86400)

    base_payload = {
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius_m,
            }
        },
        "includedTypes": list(included_types) if included_types else None,
        "maxResultCount": per_page,
    }
    base_payload = {k: v for k, v in base_payload.items() if v is not None}

    key = _cache_key("nearby", {**base_payload, "desired": desired})
    cached = cache.get(key)
    if cached is not None:
        return cached

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": settings.GOOGLE_MAPS_API_KEY,
        # Request all fields to ensure nextPageToken is returned for pagination.
        "X-Goog-FieldMask": "*",
    }

    results: List[Dict[str, Any]] = []
    payload = base_payload
    page_token = None

    while True:
        if page_token:
            payload = {"pageToken": page_token}
        resp = requests.post(f"{BASE_URL}/places:searchNearby", headers=headers, json=payload, timeout=10)
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise requests.HTTPError(f"Places nearby error {resp.status_code}: {detail}", response=resp)

        data = resp.json()
        places = data.get("places", [])
        results.extend(places)
        if len(results) >= desired:
            results = results[:desired]
            break
        page_token = data.get("nextPageToken")
        if not page_token:
            break

    cache.set(key, results, ttl)
    return results


def aggregate_nearby(
    lat: float,
    lng: float,
    radius_m: int,
    type_sets: List[List[str]],
    max_results: int,
) -> List[Dict[str, Any]]:
    """Run multiple nearby searches with different type filters and combine unique places."""

    seen = set()
    combined: List[Dict[str, Any]] = []

    for included_types in type_sets:
        if len(combined) >= max_results:
            break
        remaining = max_results - len(combined)
        chunk = nearby_search(
            lat=lat,
            lng=lng,
            radius_m=radius_m,
            included_types=included_types,
            max_results=min(remaining, max_results),
        )
        for p in chunk:
            pid = p.get("id")
            if pid and pid not in seen:
                seen.add(pid)
                combined.append(p)
            if len(combined) >= max_results:
                break

    return combined


def place_details(place_id: str, fields: Iterable[str] | None = None) -> Dict[str, Any]:
    ttl = getattr(settings, "EXPLORE_CACHE_TTL_DETAILS", 604800)
    field_mask = ",".join(fields) if fields else "id,displayName,rating,userRatingCount,formattedAddress,photos,googleMapsUri"
    key = _cache_key("details", {"place_id": place_id, "fields": field_mask})
    cached = cache.get(key)
    if cached is not None:
        return cached

    params = {
        "key": settings.GOOGLE_MAPS_API_KEY,
        "fields": field_mask,
    }
    resp = requests.get(f"{BASE_URL}/places/{place_id}", params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    cache.set(key, data, ttl)
    return data


def photo_url(photo_name: str, max_width: int = 600) -> str:
    # photo_name example: "places/ChIJ.../photos/123"
    return f"{BASE_URL}/{photo_name}/media?key={settings.GOOGLE_MAPS_API_KEY}&maxWidthPx={max_width}"
