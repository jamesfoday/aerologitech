from django.contrib import admin
from .models import AirportService, CarCategory, Car, Order, Invoice


@admin.register(AirportService)
class AirportServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "available")
    search_fields = ("name",)


@admin.register(CarCategory)
class CarCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ("brand", "model", "category", "price_per_day", "available")
    list_filter = ("category", "available")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "order_type", "service", "car", "created_at")
    list_filter = ("order_type", "created_at")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "issued_by", "amount", "paid", "created_at")
    list_filter = ("paid", "created_at")
