from django.contrib import admin
from .models import Invoice, InvoiceItem

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "user", "status", "amount", "currency", "issued_at", "created_at")
    list_filter = ("status", "currency", "issued_at", "created_at")
    search_fields = ("number", "user__username", "user__email", "user__first_name", "user__last_name")
    date_hierarchy = "issued_at"
    inlines = [InvoiceItemInline]
