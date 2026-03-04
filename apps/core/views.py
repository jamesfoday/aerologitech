from django.shortcuts import render, redirect
from apps.services.models import AirportService
from apps.explore.models import Place

def home(request):
    """Public homepage with contact POST and limited services grid."""
    if request.method == "POST":
        _ = {
            "name": request.POST.get("name", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "subject": request.POST.get("subject", "").strip(),
        }
        return redirect("home")

    services = AirportService.objects.filter(available=True).order_by("name")[:4]
    places = (
        Place.objects.filter(is_featured=True)
        .prefetch_related("images")
        .order_by("sort_order", "name")[:6]
    )

    car_teaser = [
        {"name": "Hyundai Creta", "price": "100€", "specs": "5 seats · Automatic · 2 luggage · 6.5L/100km tank"},
        {"name": "Toyota Fortuner", "price": "200€", "specs": "5 seats · Automatic · 2 luggage · 6.5L/100km tank"},
        {"name": "Toyota Hiace", "price": "100€", "specs": "7 seats · Manual · 19 luggage · 9.5L/100km tank"},
    ]

    ctx = {
        "services": services,
        "places": places,
        "page_title": "Home",
        "car_teaser": car_teaser,
    }
    return render(request, "public/home.html", ctx)

def home_about(request):
    """Public About page."""
    return render(request, "public/about.html", {"page_title": "About us"})
