from django.contrib import admin
from .models import AirportService, CarCategory, Car, Order, Invoice


@admin.register(AirportService)
class AirportServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "available")
    list_filter = ("available",)
    search_fields = ("name", "description", "tags")


@admin.register(CarCategory)
class CarCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "transmission",
        "seats",
        "luggage",
        "price",
        "available",
        "created_at",
    )
    list_filter = ("category", "transmission", "available")
    search_fields = ("name", "category__name")
    ordering = ("name",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "order_type",
        "service",
        "car",
        "start_date",
        "end_date",
        "created_at",
    )
    list_filter = ("order_type", "created_at")
    search_fields = ("user__username", "service__name", "car__name")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "issued_by", "amount", "paid", "created_at")
    list_filter = ("paid", "created_at")
    search_fields = ("order__id", "issued_by__username")
