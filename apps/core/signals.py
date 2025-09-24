from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, "profile"):
        from .models import Profile
        Profile.objects.create(user=instance)
