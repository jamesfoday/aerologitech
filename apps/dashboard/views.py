from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from apps.orders.models import Order


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

    context = {
        "labels": labels,
        "airport_series": airport_series,
        "car_series": car_series,
        "recent_services": recent_services,
        "recent_cars": recent_cars,
    }
    return render(request, "dashboard/index.html", context)
