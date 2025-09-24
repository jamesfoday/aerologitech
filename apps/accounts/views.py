# apps/accounts/views.py
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.core import signing
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q, Sum, Exists, OuterRef
from django.db.models.functions import TruncMonth
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, NoReverseMatch
from django.utils import timezone

from .forms import AddUserForm, SignUpForm
from apps.orders.models import Order

User = get_user_model()

# Optional Invoice sources (support either app if present)
InvoicesInvoice = None
ServicesInvoice = None
try:
    from apps.invoices.models import Invoice as InvoicesInvoice  # type: ignore
except Exception:
    pass
try:
    from apps.services.models import Invoice as ServicesInvoice  # type: ignore
except Exception:
    pass


# -------------------- helpers -------------------- #

def _invoice_model():
    """Return whichever Invoice model exists, or None."""
    return InvoicesInvoice or ServicesInvoice


def _is_staff(u):
    return u.is_staff or u.is_superuser


def _first_existing(names: list[str], default: str) -> str:
    """Reverse the first resolvable URL name, else return default."""
    for n in names:
        try:
            return reverse(n)
        except NoReverseMatch:
            continue
    return default


def _has_field(model, field_name: str) -> bool:
    """Safely check if a model has a field."""
    if not model:
        return False
    try:
        model._meta.get_field(field_name)
        return True
    except FieldDoesNotExist:
        return False
    except Exception:
        return False


def _user_invoices(user):
    """Return queryset of invoices for this user across schema variants."""
    Inv = _invoice_model()
    if not Inv:
        return None
    qs = Inv.objects.all()
    if _has_field(Inv, "order"):
        return qs.filter(order__user=user)
    if _has_field(Inv, "user"):
        return qs.filter(user=user)
    return qs.none()


def _paid_q(Inv):
    """Flexible 'paid' condition across differing schemas."""
    q = Q()
    if _has_field(Inv, "paid_at"):
        q |= Q(paid_at__isnull=False)
    if _has_field(Inv, "status"):
        q |= Q(status__in=["paid", "settled", "complete", "completed"])
    if _has_field(Inv, "paid"):
        q |= Q(paid=True)
    return q


def _invoice_ordering(Inv):
    """Reasonable default ordering."""
    if _has_field(Inv, "created_at"):
        return ["-created_at"]
    if _has_field(Inv, "issued_at"):
        return ["-issued_at"]
    return ["-id"]


# -------------------- AUTH (signup shares the login template tabs) -------------------- #

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("accounts:post_login")
        return render(
            request,
            "registration/login.html",
            {
                "signup_form": form,
                "form": AuthenticationForm(request),
                "active_tab": "register",
                "page_title": "Sign Up",
            },
        )

    return render(
        request,
        "registration/login.html",
        {
            "signup_form": SignUpForm(),
            "form": AuthenticationForm(request),
            "active_tab": "register",
            "page_title": "Sign Up",
        },
    )


# -------------------- USER DASHBOARD + PROFILE -------------------- #

class ProfileForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)


@login_required
def user_dashboard(request):
    """End-user dashboard with quick actions and recent orders."""
    u = request.user
    service_orders = (
        Order.objects.filter(user=u, category=Order.Category.AIRPORT_SERVICE)
        .order_by("-created_at")[:5]
    )
    car_orders = (
        Order.objects.filter(user=u, category=Order.Category.CAR_RENTAL)
        .order_by("-created_at")[:5]
    )

    ctx = {
        "page_title": "My Dashboard",
        "user_obj": u,
        "service_orders": service_orders,
        "car_orders": car_orders,
        "messages_url": reverse("accounts:my_messages"),
        "invoices_url": reverse("accounts:my_invoices"),
        "orders_url": reverse("accounts:my_orders"),
        "receipts_url": reverse("accounts:my_receipts"),
    }
    return render(request, "accounts/user_dashboard.html", ctx)


@login_required
def profile_edit(request):
    """Edit basic profile fields."""
    u = request.user
    if request.method == "POST":
        form = ProfileForm(request.POST)
        if form.is_valid():
            u.first_name = form.cleaned_data.get("first_name", "")
            u.last_name = form.cleaned_data.get("last_name", "")
            email = form.cleaned_data.get("email", "")
            if email:
                u.email = email
            u.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:dashboard")
    else:
        form = ProfileForm(
            initial={"first_name": u.first_name, "last_name": u.last_name, "email": u.email}
        )
    return render(request, "accounts/profile_edit.html", {"form": form, "page_title": "Edit Profile"})


@login_required
def post_login_redirect(request):
    """Send staff to admin dashboard; regular users to their dashboard."""
    if request.user.is_staff or request.user.is_superuser:
        return redirect("/dashboard/")
    return redirect("accounts:dashboard")


# ---------- “MY …” user-scoped pages ---------- #

@login_required
def my_orders(request):
    """User's own orders list (reuses the per-user orders view)."""
    return redirect("accounts:orders", pk=request.user.pk)


@login_required
def my_invoices(request):
    """Current user's invoices list (if invoice model exists)."""
    Inv = _invoice_model()
    if not Inv:
        messages.info(request, "Invoices section isn't configured yet.")
        return redirect("accounts:dashboard")

    qs = _user_invoices(request.user)
    if qs is None:
        messages.info(request, "Invoices section isn't configured yet.")
        return redirect("accounts:dashboard")

    sel = []
    if _has_field(Inv, "order"):
        sel.append("order")
    if _has_field(Inv, "issued_by"):
        sel.append("issued_by")
    if sel:
        qs = qs.select_related(*sel)

    invoices = qs.order_by(*_invoice_ordering(Inv))[:200]

    return render(
        request,
        "accounts/my_invoices.html",
        {"invoices": invoices, "page_title": "My Invoices"},
    )


@login_required
def my_receipts(request):
    """
    Receipts are paid invoices for the current user.
    Includes a QR code (signed token) per receipt for validation.
    Falls back to orders if no invoice model is present.
    """
    Inv = _invoice_model()
    if not Inv:
        orders = Order.objects.filter(user=request.user).order_by("-created_at")
        qr_tokens = {o.id: signing.dumps({"o": o.id, "u": request.user.id}) for o in orders}
        return render(
            request,
            "accounts/my_receipts.html",
            {"invoices": [], "orders": orders, "qr_tokens": qr_tokens, "page_title": "My Receipts"},
        )

    base_qs = _user_invoices(request.user)
    if base_qs is None:
        messages.info(request, "Receipts are not available.")
        return redirect("accounts:dashboard")

    paid_q = _paid_q(Inv)
    qs = base_qs.filter(paid_q) if paid_q.children else base_qs
    receipts = list(qs.order_by(*_invoice_ordering(Inv))[:200])

    qr_tokens = {}
    for inv in receipts:
        payload = {"i": inv.id, "u": request.user.id}
        if _has_field(Inv, "order"):
            payload["o"] = getattr(inv, "order_id", None)
        qr_tokens[inv.id] = signing.dumps(payload)

    return render(
        request,
        "accounts/my_receipts.html",
        {"invoices": receipts, "orders": [], "qr_tokens": qr_tokens, "page_title": "My Receipts"},
    )


@login_required
def my_messages(request):
    """Redirect to the site's messaging inbox for this user."""
    url = _first_existing(["messages:inbox", "messages:list", "messages_home"], "/messages/")
    return redirect(url)


# -------------------- STAFF: LIST / DETAIL / ORDERS -------------------- #

@login_required
def users_list(request):
    q = (request.GET.get("q") or "").strip()

    users = (
        User.objects
        .annotate(
            has_orders=Exists(
                Order.objects.filter(user_id=OuterRef("pk"))
            )
        )
        .order_by("-date_joined")
    )

    if q:
        users = users.filter(
            Q(username__icontains=q)
            | Q(email__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
        )

    return render(request, "accounts/users_list.html", {"users": users, "q": q})


@login_required
def user_detail(request, pk):
    u = get_object_or_404(User, pk=pk)

    # build 12-month history for this user's orders
    now = timezone.now()
    start = (now.replace(day=1) - timezone.timedelta(days=365)).replace(day=1)

    qs = (
        Order.objects.filter(user=u, created_at__gte=start)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(
            airport_total=Sum("amount", filter=Q(category=Order.Category.AIRPORT_SERVICE)),
            car_total=Sum("amount", filter=Q(category=Order.Category.CAR_RENTAL)),
        )
        .order_by("month")
    )

    labels, airport_series, car_series = [], [], []
    for row in qs:
        labels.append(row["month"].strftime("%b %Y"))
        airport_series.append(float(row.get("airport_total") or 0))
        car_series.append(float(row.get("car_total") or 0))

    phone = ""
    if hasattr(u, "profile") and getattr(u.profile, "phone", ""):
        phone = u.profile.phone

    ctx = {
        "u": u,
        "phone": phone or "",
        "labels": labels,
        "airport_series": airport_series,
        "car_series": car_series,
    }
    return render(request, "accounts/user_detail.html", ctx)


@login_required
def user_orders(request, pk):
    u = get_object_or_404(User, pk=pk)
    orders = Order.objects.filter(user=u).order_by("-created_at")
    return render(request, "accounts/user_orders.html", {"u": u, "orders": orders})


# -------------------- STAFF: ADD / DEACTIVATE / REACTIVATE / DELETE -------------------- #

@login_required
@user_passes_test(_is_staff)
def add_user(request):
    """Create a new user with username, email, full name, phone, and password."""
    if request.method == "POST":
        form = AddUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User “{user.username}” created.')
            return redirect("accounts:list")
    else:
        form = AddUserForm()
    return render(request, "accounts/add_user.html", {"form": form})


@login_required
@user_passes_test(_is_staff)
def deactivate_user(request, pk):
    """Soft-disable a user account (recommended over deletion)."""
    if request.method != "POST":
        return redirect("accounts:detail", pk=pk)

    u = get_object_or_404(User, pk=pk)
    if not u.is_active:
        messages.info(request, f'User “{u.username}” is already deactivated.')
        return redirect("accounts:detail", pk=pk)

    u.is_active = False
    u.save(update_fields=["is_active"])
    messages.success(request, f'User “{u.username}” has been deactivated.')
    return redirect("accounts:detail", pk=pk)


@login_required
@user_passes_test(_is_staff)
def reactivate_user(request, pk):
    """Re-enable a previously deactivated account."""
    if request.method != "POST":
        return redirect("accounts:detail", pk=pk)

    u = get_object_or_404(User, pk=pk)
    if u.is_active:
        messages.info(request, f'User “{u.username}” is already active.')
        return redirect("accounts:detail", pk=pk)

    u.is_active = True
    u.save(update_fields=["is_active"])
    messages.success(request, f'User “{u.username}” has been reactivated.')
    return redirect("accounts:detail", pk=pk)


@login_required
@user_passes_test(_is_staff)
def delete_user(request, pk):
    """
    Permanently delete a user (POST only).
    - Prevent deleting yourself.
    - Block delete if the user has any orders.
    - Catch ProtectedError for PROTECT FKs.
    """
    if request.method != "POST":
        return redirect("accounts:list")

    u = get_object_or_404(User, pk=pk)

    if u.id == request.user.id:
        messages.error(request, "You cannot delete yourself.")
        return redirect("accounts:list")

    if Order.objects.filter(user=u).exists():
        messages.error(
            request,
            "This user has orders and cannot be deleted. Deactivate the account instead."
        )
        return redirect("accounts:list")

    username = u.username
    try:
        u.delete()
        messages.success(request, f'User “{username}” deleted.')
    except ProtectedError:
        messages.error(
            request,
            "This user is referenced by protected records and cannot be deleted. "
            "Deactivate the account instead."
        )
    return redirect("accounts:list")


# -------------------- Receipt validation -------------------- #

@login_required
def validate_receipt(request):
    token = request.GET.get("token", "")
    try:
        payload = signing.loads(token, max_age=60 * 60 * 24 * 365)  # 1 year
    except signing.BadSignature:
        return render(request, "accounts/receipt_invalid.html", status=400)

    if payload.get("u") != request.user.id:
        return HttpResponseBadRequest("This receipt does not belong to you.")

    return render(request, "accounts/receipt_valid.html", {"payload": payload})
