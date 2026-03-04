from __future__ import annotations

from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model

User = get_user_model()


class Place(models.Model):
    CATEGORY_CHOICES = [
        ("activity", "Activity"),
        ("historical", "Historical"),
        ("nature", "Nature"),
        ("culture", "Culture"),
        ("market", "Market"),
        ("beach", "Beach"),
    ]

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    region = models.CharField(max_length=80, help_text="e.g. Banjul, Kololi, Jufureh")
    short_desc = models.TextField()
    hero_image = models.ImageField(upload_to="explore/places", blank=True, null=True)
    map_url = models.URLField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    is_featured = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            idx = 1
            while Place.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                idx += 1
                slug = f"{base}-{idx}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PlaceImage(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="explore/places/gallery")
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"Image for {self.place.name}"


class PlaceBooking(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ]

    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="bookings")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=40)
    travel_date = models.DateField()
    travelers = models.PositiveIntegerField(default=1)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} - {self.place.name}"


class AffiliateOffer(models.Model):
    OFFER_CHOICES = [
        ("hotel", "Hotel"),
        ("activity", "Activity"),
        ("flight", "Flight"),
    ]

    title = models.CharField(max_length=140)
    offer_type = models.CharField(max_length=20, choices=OFFER_CHOICES)
    region = models.CharField(max_length=80)
    teaser = models.TextField()
    provider = models.CharField(max_length=80)
    affiliate_url = models.URLField()
    image = models.ImageField(upload_to="explore/offers", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title


class ClickEvent(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    offer = models.ForeignKey(AffiliateOffer, on_delete=models.CASCADE, related_name="clicks")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referer = models.TextField(blank=True)
    utm_source = models.CharField(max_length=80, blank=True)
    utm_medium = models.CharField(max_length=80, blank=True)
    utm_campaign = models.CharField(max_length=120, blank=True)
    session_key = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Click {self.offer_id} at {self.created_at:%Y-%m-%d %H:%M}"
