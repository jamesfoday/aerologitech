from django.conf import settings  
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    display_name = models.CharField(max_length=150, blank=True, default="")
    avatar_url   = models.URLField(blank=True, default="")
    phone        = models.CharField(max_length=40, blank=True, default="")  # added
