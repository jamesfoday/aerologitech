from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

from apps.orders.models import Order
from apps.explore.models import Place, PlaceImage, PlaceBooking
from django import forms

User = get_user_model()


class DashboardProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "First name"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Last name"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email address"}),
        }


class PlaceForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = [
            "name",
            "category",
            "region",
            "short_desc",
            "map_url",
            "latitude",
            "longitude",
            "is_featured",
            "sort_order",
        ]
        widgets = {
            "short_desc": forms.Textarea(attrs={"rows": 3}),
        }


def _hide_location_fields(form: PlaceForm) -> PlaceForm:
    for field_name in ("map_url", "latitude", "longitude"):
        form.fields.pop(field_name, None)
    return form


@login_required
def dashboard_view(request):
    # ---- Sales (last 12 months), grouped by month ----
    now = timezone.now()
    start = (now.replace(day=1) - timezone.timedelta(days=365)).replace(day=1)
    sales_qs = (
        Order.objects.filter(created_at__gte=start)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(
            airport_total=Sum("amount", filter=Q(category=Order.Category.AIRPORT_SERVICE)),
            car_total=Sum("amount", filter=Q(category=Order.Category.CAR_RENTAL)),
        )
        .order_by("month")
    )

    # Build labels & datasets aligned by month
    labels = []
    airport_series = []
    car_series = []
    for row in sales_qs:
        labels.append(row["month"].strftime("%b %Y"))  # e.g., "Aug 2025"
        airport_series.append(float(row["airport_total"] or 0))
        car_series.append(float(row["car_total"] or 0))

    # ---- Recent 5 airport services ----
    recent_services = (
        Order.objects
        .filter(category=Order.Category.AIRPORT_SERVICE)
        .order_by("-created_at")[:5]
    )

    # ---- Recent 5 car rentals ----
    recent_cars = (
        Order.objects
        .filter(category=Order.Category.CAR_RENTAL)
        .order_by("-created_at")[:5]
    )

    # ---- Recent 5 tourism bookings ----
    recent_tourism = (
        PlaceBooking.objects
        .select_related("place")
        .order_by("-created_at")[:5]
    )

    context = {
        "labels": labels,
        "airport_series": airport_series,
        "car_series": car_series,
        "recent_services": recent_services,
        "recent_cars": recent_cars,
        "recent_tourism": recent_tourism,
    }
    return render(request, "dashboard/index.html", context)


@login_required
def profile_edit_view(request):
    profile_form = DashboardProfileForm(instance=request.user)
    password_form = PasswordChangeForm(user=request.user)

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "profile":
            profile_form = DashboardProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated successfully.")
                return redirect("dashboard:profile_edit")

        elif form_type == "password":
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed successfully.")
                return redirect("dashboard:profile_edit")

    return render(
        request,
        "dashboard/profile_form.html",
        {"form": profile_form, "password_form": password_form},
    )


@login_required
def places_list_view(request):
    q = request.GET.get("q", "").strip()
    places = Place.objects.all().order_by("sort_order", "name")
    if q:
        places = places.filter(Q(name__icontains=q) | Q(region__icontains=q) | Q(category__icontains=q))
    return render(request, "dashboard/places_list.html", {"places": places, "q": q})


@login_required
def places_create_view(request):
    if request.method == "POST":
        hero_files = request.FILES.getlist("hero_image")
        form = _hide_location_fields(PlaceForm(request.POST, request.FILES))
        if form.is_valid():
            place = form.save(commit=False)
            if hero_files:
                place.hero_image = hero_files[0]
            place.save()
            # extra hero files beyond first go to gallery
            for f in hero_files[1:]:
                PlaceImage.objects.create(place=place, image=f)
            return redirect("dashboard:places_list")
    else:
        form = _hide_location_fields(PlaceForm())
    return render(request, "dashboard/place_form.html", {"form": form, "is_edit": False, "place": None})


@login_required
def places_edit_view(request, pk):
    place = get_object_or_404(Place, pk=pk)
    if request.method == "POST":
        hero_files = request.FILES.getlist("hero_image")
        form = PlaceForm(request.POST, request.FILES, instance=place)
        if form.is_valid():
            place = form.save(commit=False)
            if hero_files:
                place.hero_image = hero_files[0]
            place.save()
            for f in hero_files[1:]:
                PlaceImage.objects.create(place=place, image=f)
            return redirect("dashboard:places_list")
    else:
        form = PlaceForm(instance=place)
    return render(request, "dashboard/place_form.html", {"form": form, "is_edit": True, "place": place})


@login_required
def places_delete_view(request, pk):
    place = get_object_or_404(Place, pk=pk)
    if request.method == "POST":
        place.delete()
        return redirect("dashboard:places_list")
    return render(request, "dashboard/place_delete_confirm.html", {"place": place})
