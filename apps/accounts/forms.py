# apps/accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class AddUserForm(UserCreationForm):
    email = forms.EmailField(required=False, label="Email address")
    full_name = forms.CharField(required=False, label="Full Name")
    phone = forms.CharField(required=False, label="Phone Number")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")  # password1/password2 provided by parent

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def style(name, placeholder):
            if name in self.fields:
                self.fields[name].widget.attrs.update({
                    "class": "form-control tile-input",
                    "placeholder": placeholder,
                })

        for name, ph in [
            ("username", "User name"),
            ("email", "Email address"),
            ("full_name", "Full Name"),
            ("phone", "Phone Number"),
            ("password1", "Password"),
            ("password2", "Password confirmation"),
        ]:
            style(name, ph)

        self.order_fields(["username", "email", "full_name", "phone", "password1", "password2"])

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = (self.cleaned_data.get("email") or "").strip()

        full_name = (self.cleaned_data.get("full_name") or "").strip()
        if full_name:
            parts = full_name.split()
            user.first_name = parts[0]
            user.last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        if commit:
            user.save()
            phone = (self.cleaned_data.get("phone") or "").strip()
            try:
                profile = getattr(user, "profile", None)
                if profile is not None and hasattr(profile, "phone"):
                    profile.phone = phone
                    profile.save()
            except Exception:
                pass
        return user


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email address")
    phone = forms.CharField(max_length=30, required=False, label="Phone Number")
    first_name = forms.CharField(max_length=150, required=False, label="First name")
    last_name = forms.CharField(max_length=150, required=False, label="Last name")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = (self.cleaned_data.get("email") or "").strip()
        user.first_name = (self.cleaned_data.get("first_name") or "").strip()
        user.last_name = (self.cleaned_data.get("last_name") or "").strip()

        if commit:
            user.save()
            phone = (self.cleaned_data.get("phone") or "").strip()
            try:
                profile = getattr(user, "profile", None)
                if profile is not None and hasattr(profile, "phone") and phone:
                    profile.phone = phone
                    profile.save(update_fields=["phone"])
            except Exception:
                pass
        return user
