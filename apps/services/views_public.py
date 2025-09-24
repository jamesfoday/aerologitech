from django.shortcuts import render
from .models import AirportService, Car

def airport_services_public(request):
    services = AirportService.objects.filter(available=True).order_by("name")
    ctx = {"services": services, "page_title": "Airport Services • Catalog"}
    return render(request, "services/public/airport_services.html", ctx)

def cars_catalog_placeholder(request):
    cars = Car.objects.filter(available=True).order_by("name")
    ctx = {"cars": cars, "page_title": "Car Rental • Catalog"}
    return render(request, "services/public/cars_catalog_placeholder.html", ctx)
