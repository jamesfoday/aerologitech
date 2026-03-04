from django.contrib import admin

from .models import Place, AffiliateOffer, ClickEvent, PlaceBooking


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "region", "is_featured", "sort_order")
    list_filter = ("category", "region", "is_featured")
    search_fields = ("name", "region", "short_desc")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("sort_order", "name")


@admin.register(AffiliateOffer)
class AffiliateOfferAdmin(admin.ModelAdmin):
    list_display = ("title", "offer_type", "region", "provider", "is_active", "sort_order")
    list_filter = ("offer_type", "region", "is_active")
    search_fields = ("title", "provider", "region", "teaser")
    ordering = ("sort_order", "title")


@admin.register(ClickEvent)
class ClickEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "offer", "user", "ip_address", "utm_source", "utm_medium")
    list_filter = ("offer__offer_type", "offer__provider", "utm_source", "utm_campaign")
    search_fields = ("offer__title", "ip_address", "user_agent", "referer", "utm_source", "utm_campaign")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(PlaceBooking)
class PlaceBookingAdmin(admin.ModelAdmin):
    list_display = ("created_at", "place", "full_name", "email", "travel_date", "travelers", "status")
    list_filter = ("status", "travel_date", "place__region")
    search_fields = ("full_name", "email", "phone", "place__name")
    ordering = ("-created_at",)
