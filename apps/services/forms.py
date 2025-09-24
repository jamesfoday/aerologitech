# apps/services/forms.py
from django import forms
from django.utils import timezone
from .models import AirportService, Car

BASE_INP = {"class": "w-100 bg-transparent", "style": "border:none;outline:none;"}


# =========================
# Airport Service Forms
# =========================
class AirportServiceForm(forms.ModelForm):
    class Meta:
        model = AirportService
        fields = ["image", "name", "description", "price", "available"]
        labels = {
            "image": "Upload an image",
            "name": "Overview",
            "description": "Description",
            "price": "Price",
            "available": "Available",
        }
        widgets = {
            "image": forms.ClearableFileInput(attrs={**BASE_INP, "accept": "image/*"}),
            "name": forms.TextInput(attrs={**BASE_INP, "placeholder": "Short overview / title"}),
            "description": forms.Textarea(
                attrs={**BASE_INP, "rows": 4, "placeholder": "Describe the service"}
            ),
            "price": forms.NumberInput(attrs={**BASE_INP, "step": "0.01", "min": "0"}),
            "available": forms.CheckboxInput(),
        }


class ServiceBookingForm(forms.Form):
    """
    Simple booking form to match the mock:
    - date picker
    - optional terms/notes textarea
    """
    date = forms.DateField(
        label="",
        widget=forms.DateInput(attrs={**BASE_INP, "type": "date", "placeholder": "MM/DD/YYYY"}),
    )
    terms = forms.CharField(
        label="Terms & Condition",
        required=False,
        widget=forms.Textarea(attrs={**BASE_INP, "rows": 4, "placeholder": "Any conditions or notes…"}),
    )

    def clean_date(self):
        d = self.cleaned_data["date"]
        if d < timezone.localdate():
            raise forms.ValidationError("Please pick a date today or later.")
        return d


# =========================
# Car Forms
# =========================
class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = [
            "image",
            "name",
            "category",       # optional in model; helpful for filtering
            "seats",
            "transmission",
            "luggage",
            "tank",
            "price",
            "available",
        ]
        labels = {
            "image": "Upload an image",
            "name": "Car name",
            "category": "Category",
            "seats": "Seats",
            "transmission": "Transmission",
            "luggage": "Luggage",
            "tank": "Tank",
            "price": "Price",
            "available": "Available",
        }
        widgets = {
            "image": forms.ClearableFileInput(attrs={**BASE_INP, "accept": "image/*"}),
            "name": forms.TextInput(attrs={**BASE_INP, "placeholder": "e.g. Toyota Corolla"}),
            "category": forms.Select(attrs={**BASE_INP}),
            "seats": forms.NumberInput(attrs={**BASE_INP, "step": "1", "min": "0"}),
            # choices come from the model; Select will render them
            "transmission": forms.Select(attrs={**BASE_INP}),
            "luggage": forms.NumberInput(attrs={**BASE_INP, "step": "1", "min": "0"}),
            "tank": forms.TextInput(attrs={**BASE_INP, "placeholder": "e.g. Full to full"}),
            "price": forms.NumberInput(attrs={**BASE_INP, "step": "0.01", "min": "0"}),
            "available": forms.CheckboxInput(),
        }

    # Light validation & normalization
    def clean_name(self):
        return (self.cleaned_data.get("name") or "").strip()

    def clean_seats(self):
        v = self.cleaned_data.get("seats") or 0
        if v < 0:
            raise forms.ValidationError("Seats cannot be negative.")
        return v

    def clean_luggage(self):
        v = self.cleaned_data.get("luggage") or 0
        if v < 0:
            raise forms.ValidationError("Luggage cannot be negative.")
        return v

    def clean_price(self):
        v = self.cleaned_data.get("price") or 0
        if v < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return v
