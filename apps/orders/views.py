from __future__ import annotations

import json
from datetime import timedelta, datetime

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Order
from apps.services.models import AirportService, Car


@login_required
def orders_list(request: HttpRequest):
    q = (request.GET.get("q") or "").strip()
    date_range = (request.GET.get("range") or "").lower()
    qs = Order.objects.all().order_by("-created_at")

    if q:
        qs = qs.filter(
            Q(customer_name__icontains=q)
            | Q(status__icontains=q)
            | Q(category__icontains=q)
        )

    if date_range in {"week", "7"}:
        since = timezone.now() - timedelta(days=7)
        qs = qs.filter(created_at__gte=since)
    elif date_range in {"month", "30"}:
        since = timezone.now() - timedelta(days=30)
        qs = qs.filter(created_at__gte=since)

    page_obj = Paginator(qs, 15).get_page(request.GET.get("page"))
    return render(request, "orders/orders_list.html", {
        "q": q,
        "date_range": date_range,
        "page_obj": page_obj,
    })


@login_required
def order_detail(request: HttpRequest, pk: int):
    o = get_object_or_404(Order, pk=pk)
    return render(request, "orders/order_detail.html", {"o": o})


@login_required
def order_thanks(request: HttpRequest, pk: int):
    """
    User-facing receipt page after a successful booking.
    """
    o = get_object_or_404(Order, pk=pk)
    return render(request, "orders/order_thanks.html", {"o": o})


@login_required
@require_POST
def order_create(request: HttpRequest):
    """
    Accept JSON from the booking modal and create an Order.
    """
    try:
        if request.content_type and "application/json" in request.content_type:
            payload = json.loads(request.body.decode("utf-8"))
        else:
            payload = request.POST.dict()
    except Exception:
        return JsonResponse({"error": "Invalid payload."}, status=400)

    object_type = (payload.get("object_type") or "").lower()
    object_id = payload.get("object_id")
    when_str = payload.get("when") or ""
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip()
    phone = (payload.get("phone") or "").strip()

    if not (object_type and object_id and name and email and phone and when_str):
        return JsonResponse({"error": "Missing required fields."}, status=400)

    # date/time parse
    try:
        dt = datetime.fromisoformat(when_str)
    except Exception:
        try:
            dt = timezone.make_aware(datetime.strptime(when_str, "%Y-%m-%dT%H:%M"))
        except Exception:
            return JsonResponse({"error": "Invalid date/time."}, status=400)

    # look up item + derive totals/meta
    if object_type == "service":
        obj = get_object_or_404(AirportService, pk=object_id)
        category = Order.Category.AIRPORT_SERVICE
        amount = obj.price or 0
        currency = "EUR"
        meta = {
            "service_id": obj.id,
            "service_name": obj.name,
            "when": dt.isoformat(),
            "email": email,
            "phone": phone,
        }
    elif object_type == "car":
        obj = get_object_or_404(Car, pk=object_id)
        category = Order.Category.CAR_RENTAL
        amount = obj.price or 0
        currency = "EUR"
        meta = {
            "car_id": obj.id,
            "car_name": obj.name,
            "when": dt.isoformat(),
            "email": email,
            "phone": phone,
        }
    else:
        return JsonResponse({"error": "Unknown object type."}, status=400)

    o = Order.objects.create(
        user=request.user,
        category=category,
        amount=amount,
        currency=currency,
        status=Order.Status.PAID,  # keep or change to PENDING as you prefer
        customer_name=name,
        meta=meta,
    )

    # Redirect regular users to a receipt; admins could still navigate to list.
    return JsonResponse({
        "ok": True,
        "order_id": o.id,
        "redirect": reverse("orders:thanks", args=[o.id]),
    })
