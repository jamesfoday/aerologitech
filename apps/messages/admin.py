from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sender",
        "recipient",
        "short_body",
        "is_read",
        "created_at",
    )
    list_filter = ("is_read", "created_at")
    search_fields = ("body", "sender__username", "recipient__username")
    ordering = ("-created_at",)

    def short_body(self, obj):
        return (obj.body[:50] + "...") if len(obj.body) > 50 else obj.body
    short_body.short_description = "Message"
