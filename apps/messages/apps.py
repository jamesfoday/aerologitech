from django.apps import AppConfig

class AircarMessagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.messages"          # path to your app package
    label = "aircar_messages"       # <-- unique label to avoid clash
