# apps/invoices/models.py
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SENT = "SENT", "Sent"
        PAID = "PAID", "Paid"
        VOID = "VOID", "Void"

    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="invoices")
    number      = models.CharField(max_length=32, unique=True, blank=True)
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True)
    currency    = models.CharField(max_length=3, default="EUR")
    tax_rate    = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))  # e.g. 20.00 = 20%
    issued_at   = models.DateField(default=timezone.now)
    due_at      = models.DateField(null=True, blank=True)
    paid_at     = models.DateField(null=True, blank=True)
    notes       = models.TextField(blank=True, default="")
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)

    # cached total
    amount      = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    def __str__(self):
        return self.number or f"Invoice #{self.pk}"

    @property
    def subtotal(self) -> Decimal:
        """Sum of qty * unit_price across items. 0.00 if not yet saved (no PK)."""
        if not self.pk:
            return Decimal("0.00")
        agg = self.items.aggregate(s=models.Sum(models.F("qty") * models.F("unit_price")))
        return (agg["s"] or Decimal("0.00")).quantize(Decimal("0.01"))

    @property
    def tax_amount(self) -> Decimal:
        return (self.subtotal * (self.tax_rate / Decimal("100"))).quantize(Decimal("0.01"))

    @property
    def total(self) -> Decimal:
        return (self.subtotal + self.tax_amount).quantize(Decimal("0.01"))

    def save(self, *args, **kwargs):
        """
        First save (no PK yet): create number, save once to get PK,
        then compute cached amount and update.
        Subsequent saves: recompute cached amount and save.
        """
        creating = self.pk is None

        # Generate invoice number if missing
        if not self.number:
            today = timezone.now()
            yyyymm = today.strftime("%Y%m")
            prefix = f"INV-{yyyymm}-"
            last = Invoice.objects.filter(number__startswith=prefix).order_by("-number").first()
            if last and last.number:
                try:
                    seq = int(last.number.split("-")[-1]) + 1
                except Exception:
                    seq = 1
            else:
                seq = 1
            self.number = f"{prefix}{seq:04d}"

        if creating:
            # Save once to obtain PK (can't read self.items before PK exists)
            kwargs.pop("update_fields", None)  # ensure full insert
            super().save(*args, **kwargs)
            # Now compute and cache amount
            self.amount = self.total
            super().save(update_fields=["amount"])
        else:
            self.amount = self.total
            super().save(*args, **kwargs)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]


class InvoiceItem(models.Model):
    invoice     = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=255)
    qty         = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"))
    unit_price  = models.DecimalField(max_digits=10, decimal_places=2)

    def line_total(self) -> Decimal:
        return (self.qty * self.unit_price).quantize(Decimal("0.01"))

    def __str__(self):
        return f"{self.description} ({self.qty} × {self.unit_price})"


# --- Keep cached amount in sync when items change ---

@receiver(post_save, sender=InvoiceItem)
def _recalc_amount_on_item_save(sender, instance: InvoiceItem, **kwargs):
    inv = instance.invoice
    # Avoid recursion storm: update amount only
    inv.amount = inv.total
    Invoice.objects.filter(pk=inv.pk).update(amount=inv.amount)

@receiver(post_delete, sender=InvoiceItem)
def _recalc_amount_on_item_delete(sender, instance: InvoiceItem, **kwargs):
    inv = instance.invoice
    inv.amount = inv.total
    Invoice.objects.filter(pk=inv.pk).update(amount=inv.amount)
