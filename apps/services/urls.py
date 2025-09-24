# apps/services/urls.py
from django.urls import path
from .views import (
    service_list, service_create, service_detail, service_book,
    car_list, car_create, car_update, car_delete, car_detail,
    service_delete, service_update,
)
from .views_public import airport_services_public, cars_catalog_placeholder

app_name = "services"

urlpatterns = [
    # services (dashboard)
    path("", service_list, name="list"),
    path("add/", service_create, name="create"),
    path("<int:pk>/", service_detail, name="detail"),
    path("<int:pk>/book/", service_book, name="book"),
    path("<int:pk>/delete/", service_delete, name="delete"),
    path("<int:pk>/edit/", service_update, name="edit"),

    # cars (dashboard)
    path("cars/", car_list, name="car_list"),
    path("cars/add/", car_create, name="car_create"),
    path("cars/<int:pk>/edit/", car_update, name="car_update"),
    path("cars/<int:pk>/delete/", car_delete, name="car_delete"),
    path("cars/<int:pk>/", car_detail, name="car_detail"),

    # public catalog
    path("catalog/airport/", airport_services_public, name="catalog_airport"),
    path("catalog/cars/", cars_catalog_placeholder, name="catalog_cars"),
]
