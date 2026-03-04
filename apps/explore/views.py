from __future__ import annotations

from django.conf import settings
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_GET
from django.urls import reverse

from .models import Place
from .forms import PlaceBookingForm

CATEGORIES = [
    {"code": "historical", "label": "Historical"},
    {"code": "activity", "label": "Activities"},
    {"code": "nature", "label": "Nature"},
    {"code": "culture", "label": "Culture"},
]


def gambia_page(request: HttpRequest) -> HttpResponse:
    desired = max(int(getattr(settings, "EXPLORE_MAX_RESULTS", 20)), 1)
    initial_places = (
        Place.objects.filter(is_featured=True)
        .prefetch_related("images")
        .order_by("sort_order", "name")[:desired]
    )

    return render(
        request,
        "explore/gambia.html",
        {
            "page_title": "Explore The Gambia",
            "categories": CATEGORIES,
            "initial_places": initial_places,
        },
    )


@require_GET
def nearby(request: HttpRequest) -> HttpResponse:
    category = request.GET.get("type")

    places_qs = (
        Place.objects.filter(is_featured=True)
        .prefetch_related("images")
        .order_by("sort_order", "name")
    )
    valid_categories = {choice[0] for choice in Place.CATEGORY_CHOICES}
    if category in valid_categories:
        places_qs = places_qs.filter(category=category)

    if request.headers.get("HX-Request"):
        return render(request, "explore/partials/_places_cards.html", {"places": places_qs})

    places = []
    for place in places_qs:
        first_gallery = place.images.first()
        places.append(
            {
                "id": place.id,
                "name": place.name,
                "slug": place.slug,
                "category": place.category,
                "region": place.region,
                "short_desc": place.short_desc,
                "map_url": place.map_url,
                "hero_image": (
                    place.hero_image.url
                    if place.hero_image
                    else (first_gallery.image.url if first_gallery else "")
                ),
            }
        )

    return JsonResponse({"places": places})


def place_detail(request: HttpRequest, slug: str) -> HttpResponse:
    place = get_object_or_404(Place, slug=slug)
    if request.method == "POST":
        booking_form = PlaceBookingForm(request.POST)
        if booking_form.is_valid():
            booking = booking_form.save(commit=False)
            booking.place = place
            if request.user.is_authenticated:
                booking.user = request.user
            booking.save()
            detail_url = reverse("explore:place_detail", kwargs={"slug": place.slug})
            return redirect(f"{detail_url}?booked=1")
    else:
        booking_form = PlaceBookingForm(initial={"travelers": 1})

    return render(
        request,
        "explore/place_detail.html",
        {
            "place": place,
            "page_title": place.name,
            "booking_form": booking_form,
            "booking_success": request.GET.get("booked") == "1",
        },
    )
