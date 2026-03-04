from django import forms

from .models import PlaceBooking


class PlaceBookingForm(forms.ModelForm):
    class Meta:
        model = PlaceBooking
        fields = ["full_name", "email", "phone", "travel_date", "travelers", "message"]
        widgets = {
            "travel_date": forms.DateInput(attrs={"type": "date"}),
            "travelers": forms.NumberInput(attrs={"min": 1}),
            "message": forms.Textarea(attrs={"rows": 4, "placeholder": "Tell us your preferred schedule or notes"}),
        }
