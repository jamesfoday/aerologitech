# apps/invoices/forms.py
from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
import re

from .models import Invoice, InvoiceItem

INPUT_CLS = {"class": "w-100 bg-transparent", "style": "border:none;outline:none;"}


class InvoiceForm(forms.ModelForm):
    # Alias so templates can use {{ form.note }} while model uses "notes"
    note = forms.CharField(
        required=False,
        label="Note",
        widget=forms.Textarea(attrs={"rows": 2, **INPUT_CLS}),
    )
    # NEW: send email right after creating
    send_now = forms.BooleanField(
        required=False,
        initial=True,
        label="Email this invoice to the customer after creating",
        widget=forms.CheckboxInput(),
    )

    class Meta:
        model = Invoice
        # Do NOT include "notes" here; we handle it via the 'note' alias
        fields = ("user", "status", "currency", "tax_rate", "issued_at", "due_at")
        labels = {
            "user": "Customer",
            "status": "Status",
            "currency": "Currency",
            "tax_rate": "Tax Rate (%)",
            "issued_at": "Issued at",
            "due_at": "Due at",
        }
        widgets = {
            "user":     forms.Select(attrs=INPUT_CLS),
            "status":   forms.Select(attrs=INPUT_CLS),
            "currency": forms.TextInput(attrs={
                **INPUT_CLS,
                "placeholder": "e.g. EUR",
                "inputmode": "latin",
                "autocomplete": "off",
                "pattern": "[A-Za-z]{3,}",
                "style": INPUT_CLS["style"] + " text-transform:uppercase;",
            }),
            "tax_rate": forms.NumberInput(attrs={"step": "0.01", "min": "0", **INPUT_CLS}),
            "issued_at": forms.DateInput(attrs={"type": "date", **INPUT_CLS}),
            "due_at":    forms.DateInput(attrs={"type": "date", **INPUT_CLS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Seed alias from model field
        if self.instance and getattr(self.instance, "notes", None):
            self.fields["note"].initial = self.instance.notes

    def clean_currency(self):
        val = (self.cleaned_data.get("currency") or "").strip()
        if not re.fullmatch(r"[A-Za-z]{3,}", val):
            raise ValidationError("Currency must be letters only (e.g., USD, EUR).")
        return val.upper()

    def clean_tax_rate(self):
        v = self.cleaned_data.get("tax_rate")
        return v or 0

    def save(self, commit=True):
        obj = super().save(commit=False)
        # Write alias back to model field
        obj.notes = self.cleaned_data.get("note", "") or ""
        if commit:
            obj.save()
            if hasattr(self, "save_m2m"):
                self.save_m2m()
        return obj


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ("description", "qty", "unit_price")
        labels = {
            "description": "Description",
            "qty": "Qty",
            "unit_price": "Unit price",
        }
        widgets = {
            "description": forms.TextInput(attrs={**INPUT_CLS, "placeholder": "Describe the item/service"}),
            "qty":         forms.NumberInput(attrs={"step": "1", "min": "0", **INPUT_CLS}),
            "unit_price":  forms.NumberInput(attrs={"step": "0.01", "min": "0", **INPUT_CLS}),
        }


InvoiceItemFormSet = inlineformset_factory(
    Invoice, InvoiceItem, form=InvoiceItemForm, extra=1, can_delete=True
)
