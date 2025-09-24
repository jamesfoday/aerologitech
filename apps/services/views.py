# apps/services/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import AirportService, Car
from .forms import AirportServiceForm, ServiceBookingForm, CarForm
from django.db.models.deletion import ProtectedError


# =========================
# Airport Services
# =========================

@login_required
def service_list(request):
    q = (request.GET.get("q") or "").strip()
    qs = AirportService.objects.all()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
    return render(request, "services/service_list.html", {"services": qs, "q": q})


@login_required
def service_create(request):
    if request.method == "POST":
        form = AirportServiceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Service created.")
            return redirect("services:list")
        messages.error(request, "Please correct the errors below.")
    else:
        form = AirportServiceForm(initial={"available": True})
    return render(request, "services/service_form.html", {"form": form, "mode": "create"})


# @login_required
def service_detail(request, pk: int):
    svc = get_object_or_404(AirportService, pk=pk)
    rel_qs = AirportService.objects.exclude(pk=svc.pk)

    tags_csv = getattr(svc, "tags", "") or ""
    tag_list = [t.strip() for t in tags_csv.split(",") if t.strip()]

    q = Q()
    if tag_list:
        for t in tag_list[:6]:
            q |= Q(name__icontains=t) | Q(description__icontains=t)
    else:
        import re
        def words(text: str):
            toks = re.findall(r"[A-Za-z]{3,}", (text or "").lower())
            seen, out = set(), []
            for t in toks:
                if t not in seen:
                    seen.add(t)
                    out.append(t)
            return out
        for w in (words(svc.name) + words(svc.description))[:6]:
            q |= Q(name__icontains=w) | Q(description__icontains=w)
    if q:
        rel_qs = rel_qs.filter(q)

    related = rel_qs.order_by("name")[:6]
    return render(
        request,
        "services/service_detail.html",
        {"svc": svc, "related": related, "tags": tag_list},
    )


@login_required
def service_book(request, pk: int):
    svc = get_object_or_404(AirportService, pk=pk)
    if request.method == "POST":
        form = ServiceBookingForm(request.POST)
        if form.is_valid():
            when = form.cleaned_data["date"]
            messages.success(
                request,
                f"Your booking for “{svc.name}” on {when:%b %d, %Y} has been recorded.",
            )
            return redirect("services:detail", pk=svc.pk)
        messages.error(request, "Please choose a valid date.")
    else:
        form = ServiceBookingForm()
    return render(request, "services/service_book.html", {"svc": svc, "form": form})


# =========================
# Cars
# =========================

@login_required
def car_list(request):
    q = (request.GET.get("q") or "").strip()
    cars_qs = Car.objects.select_related("category").all().order_by("name")
    if q:
        cars_qs = cars_qs.filter(
            Q(name__icontains=q)
            | Q(transmission__icontains=q)
            | Q(category__name__icontains=q)
        )

    paginator = Paginator(cars_qs, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    ctx = {"q": q, "page_obj": page_obj, "cars": page_obj.object_list}
    return render(request, "services/car_list.html", ctx)


@login_required
def car_create(request):
    """Always publish new cars so they appear on the public catalog."""
    if request.method == "POST":
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            car = form.save(commit=False)
            car.available = True  # force visible on public page
            car.save()
            messages.success(request, f'Car “{car.name}” created.')
            return redirect("services:car_list")
        messages.error(request, "Please correct the errors below.")
    else:
        form = CarForm(initial={"available": True})
    return render(request, "services/car_form.html", {"form": form, "mode": "create"})


@login_required
def car_update(request, pk: int):
    """Preserve availability unless explicitly posted."""
    car = get_object_or_404(Car, pk=pk)
    if request.method == "POST":
        form = CarForm(request.POST, request.FILES, instance=car)
        original_available = car.available
        if form.is_valid():
            car = form.save(commit=False)
            # If the checkbox wasn't submitted (field not rendered), keep original value
            if "available" not in request.POST:
                car.available = original_available if original_available is not None else True
            car.save()
            messages.success(request, f'Car “{car.name}” updated.')
            return redirect("services:car_list")
        messages.error(request, "Please correct the errors below.")
    else:
        form = CarForm(instance=car)
    return render(
        request,
        "services/car_form.html",
        {"form": form, "mode": "edit", "car": car},
    )


@login_required
@require_POST
def car_delete(request, pk: int):
    car = get_object_or_404(Car, pk=pk)
    name = car.name
    car.delete()
    messages.success(request, f'Car “{name}” has been deleted.')
    return redirect("services:car_list")


@login_required
def car_detail(request, pk: int):
    car = get_object_or_404(Car.objects.select_related("category"), pk=pk)
    return render(request, "services/car_detail.html", {"car": car})


@login_required
@require_POST
def service_delete(request, pk: int):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to delete services.")
        return redirect("services:list")

    svc = get_object_or_404(AirportService, pk=pk)
    name = svc.name
    try:
        svc.delete()
        messages.success(request, f'“{name}” deleted.')
    except ProtectedError:
        messages.error(
            request,
            f'“{name}” cannot be deleted because it is referenced by other records.'
        )
    return redirect("services:list")


@login_required
def service_update(request, pk: int):
    svc = get_object_or_404(AirportService, pk=pk)
    if request.method == "POST":
        form = AirportServiceForm(request.POST, request.FILES, instance=svc)
        if form.is_valid():
            form.save()
            messages.success(request, f'Service “{svc.name}” updated.')
            return redirect("services:list")
        messages.error(request, "Please correct the errors below.")
    else:
        form = AirportServiceForm(instance=svc)
    return render(
        request,
        "services/service_form.html",
        {"form": form, "mode": "edit", "svc": svc},
    )
