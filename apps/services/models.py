from django.conf import settings
from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator


class AirportService(models.Model):
    """Sellable airport service shown in public catalog."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    available = models.BooleanField(default=True, db_index=True)
    image = models.ImageField(upload_to="services/", blank=True, null=True)
    tags = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["available", "name"]),
            models.Index(fields=["price"]),
        ]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("services:detail", args=[self.pk])


class CarCategory(models.Model):
    """Optional grouping for cars (e.g., Economy, SUV)."""

    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Car categories"

    def __str__(self) -> str:
        return self.name


class Car(models.Model):
    """Car available for rental."""

    TRANSMISSION_CHOICES = [
        ("manual", "Manual"),
        ("automatic", "Automatic"),
    ]

    name = models.CharField(max_length=120)
    category = models.ForeignKey(
        CarCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="cars"
    )
    image = models.ImageField(upload_to="cars/", blank=True, null=True)

    seats = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    transmission = models.CharField(
        max_length=12, choices=TRANSMISSION_CHOICES, default="automatic"
    )
    luggage = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    tank = models.CharField(max_length=60, blank=True)

    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    available = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["available", "name"]),
            models.Index(fields=["price"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("services:car_detail", args=[self.pk])

    @property
    def specs_text(self) -> str:
        """Compact spec line for cards."""
        parts = []
        if self.seats:
            parts.append(f"{self.seats} seats")
        if self.transmission:
            parts.append(self.transmission.title())
        if self.luggage:
            parts.append(f"{self.luggage} luggage")
        if self.tank:
            parts.append(self.tank)
        return " • ".join(parts)


class Order(models.Model):
    """Order for either a service or a car."""

    ORDER_TYPES = (
        ("service", "Airport Service"),
        ("car", "Car Rental"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    order_type = models.CharField(max_length=10, choices=ORDER_TYPES)

    service = models.ForeignKey(
        AirportService, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders"
    )
    car = models.ForeignKey(
        Car, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders"
    )

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order {self.id} by {self.user}"

    def clean(self):
        """Validate that exactly one item matches order_type."""
        from django.core.exceptions import ValidationError

        if self.order_type == "service":
            if not self.service or self.car:
                raise ValidationError("Service orders must reference a service only.")
        elif self.order_type == "car":
            if not self.car or self.service:
                raise ValidationError("Car orders must reference a car only.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Invoice(models.Model):
    """Invoice for a single order."""

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="invoice"
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invoices_issued"
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    paid = models.BooleanField(default=False, db_index=True)

    def __str__(self) -> str:
        return f"Invoice {self.id} for Order {self.order.id}"
