from django.shortcuts import render, redirect
from apps.services.models import AirportService

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
    ctx = {"services": services, "page_title": "Home"}
    return render(request, "public/home.html", ctx)

def home_about(request):
    """Public About page."""
    return render(request, "public/about.html", {"page_title": "About us"})
