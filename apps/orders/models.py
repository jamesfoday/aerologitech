# apps/orders/models.py
from django.db import models

class Order(models.Model):
    class Category(models.TextChoices):
        AIRPORT_SERVICE = "AIRPORT_SERVICE", "Airport Service"
        CAR_RENTAL      = "CAR_RENTAL", "Car Rental"

    class Status(models.TextChoices):
        PENDING  = "PENDING", "Pending"
        PAID     = "PAID", "Paid"
        CANCELED = "CANCELED", "Canceled"
        REFUNDED = "REFUNDED", "Refunded"

    category      = models.CharField(max_length=32, choices=Category.choices, db_index=True)
    amount        = models.DecimalField(max_digits=10, decimal_places=2)
    currency      = models.CharField(max_length=3, default="EUR")
    status        = models.CharField(max_length=16, choices=Status.choices, default=Status.PAID, db_index=True)
    customer_name = models.CharField(max_length=150, blank=True, default="")
    created_at    = models.DateTimeField(auto_now_add=True, db_index=True)
    meta          = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.get_category_display()} {self.amount} {self.currency} ({self.status})"

    class Meta:
        indexes = [
            models.Index(fields=["category", "created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]
