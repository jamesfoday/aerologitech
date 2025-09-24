# apps/invoices/views.py
from io import BytesIO
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from .forms import InvoiceForm, InvoiceItemFormSet
from .models import Invoice


def _is_staff(u):
    return u.is_staff or u.is_superuser


# ---------- List & Detail ----------

@login_required
def invoice_list(request):
    """
    Invoice index page with search + pagination.
    We pre-compute a pagination window so the template has no < or > logic.
    """
    q = (request.GET.get("q") or "").strip()
    invoices_qs = Invoice.objects.select_related("user").order_by("-created_at")
    if q:
        invoices_qs = invoices_qs.filter(
            Q(number__icontains=q)
            | Q(user__username__icontains=q)
            | Q(user__email__icontains=q)
            | Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
        )

    paginator = Paginator(invoices_qs, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # ---- pagination window ----
    current = page_obj.number
    num_pages = paginator.num_pages

    start = max(1, current - 1)
    end = min(num_pages, current + 1)
    window_pages = list(range(start, end + 1))

    show_left_ellipsis = start > 2
    show_right_ellipsis = end < num_pages - 1

    context = {
        "q": q,
        "page_obj": page_obj,
        "invoices": page_obj.object_list,
        "num_pages": num_pages,
        "current": current,
        "window_pages": window_pages,
        "show_left_ellipsis": show_left_ellipsis,
        "show_right_ellipsis": show_right_ellipsis,
        "first_page": 1,
        "last_page": num_pages,
        "prev_page": current - 1 if page_obj.has_previous() else current,
        "next_page": current + 1 if page_obj.has_next() else current,
    }
    return render(request, "invoices/invoice_list.html", context)


@login_required
def invoice_detail(request, pk):
    inv = get_object_or_404(
        Invoice.objects.select_related("user").prefetch_related("items"), pk=pk
    )
    return render(request, "invoices/invoice_detail.html", {"inv": inv})


# ---------- Create / Update / Delete ----------

@login_required
@user_passes_test(_is_staff)
def invoice_create(request):
    if request.method == "POST":
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            inv = form.save(commit=False)
            inv.amount = Decimal("0.00")
            inv.save()

            formset.instance = inv
            formset.save()

            inv.amount = inv.total
            inv.save(update_fields=["amount"])

            if form.cleaned_data.get("send_now"):
                if _email_invoice_to_customer(request, inv):
                    messages.success(
                        request,
                        f"Invoice {inv.number} created and emailed to {inv.user.email}.",
                    )
                else:
                    messages.warning(
                        request,
                        f"Invoice {inv.number} created, but the customer has no email.",
                    )
            else:
                messages.success(request, f"Invoice {inv.number} created.")

            return redirect("invoices:detail", pk=inv.pk)
    else:
        form = InvoiceForm()
        formset = InvoiceItemFormSet()

    return render(
        request, "invoices/invoice_form.html", {"form": form, "formset": formset}
    )


@login_required
@user_passes_test(_is_staff)
def invoice_update(request, pk):
    inv = get_object_or_404(Invoice, pk=pk)
    if request.method == "POST":
        form = InvoiceForm(request.POST, instance=inv)
        formset = InvoiceItemFormSet(request.POST, instance=inv)
        if form.is_valid() and formset.is_valid():
            inv = form.save(commit=False)
            inv.save()
            formset.save()
            inv.amount = inv.total
            inv.save(update_fields=["amount"])

            messages.success(request, f"Invoice {inv.number} updated.")
            return redirect("invoices:detail", pk=inv.pk)
    else:
        form = InvoiceForm(instance=inv)
        formset = InvoiceItemFormSet(instance=inv)

    return render(
        request,
        "invoices/invoice_form.html",
        {"form": form, "formset": formset, "inv": inv},
    )


@login_required
@user_passes_test(_is_staff)
@require_POST
def invoice_delete(request, pk):
    """Delete an invoice (POST only)."""
    inv = get_object_or_404(Invoice, pk=pk)
    number = inv.number
    inv.delete()
    messages.success(request, f"Invoice {number} deleted.")
    return redirect("invoices:list")


# ---------- PDF helpers ----------

def _money(v: Decimal, currency: str) -> str:
    return f"{v:.2f} {currency}"


def _render_pdf_html(request, inv) -> str:
    ctx = {"inv": inv, "base_url": request.build_absolute_uri("/")}
    return render_to_string("invoices/pdf.html", ctx, request=request)


def _reportlab_invoice_pdf(inv) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        title=f"Invoice {inv.number}",
    )

    styles = getSampleStyleSheet()
    H = styles["Heading2"]; H.alignment = 1
    P = styles["BodyText"]

    story = []
    story.append(Paragraph("AeroLogicTech", H))
    story.append(Paragraph(f"<b>Invoice</b> &nbsp; {inv.number}", P))
    story.append(Spacer(1, 6))

    meta = [
        ["Billed to:", inv.user.get_full_name() or inv.user.username],
        ["Issue date:", inv.issued_at.strftime("%d %b %Y")],
        ["Due date:", inv.due_at.strftime("%d %b %Y") if inv.due_at else "—"],
        ["Status:", inv.status],
    ]
    t_meta = Table(meta, colWidths=[35 * mm, None])
    t_meta.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 8))

    data = [["No", "Description", "Qty", "Unit price", "Total"]]
    for i, it in enumerate(inv.items.all(), start=1):
        total = (it.qty * it.unit_price)
        data.append([
            f"{i:02d}",
            it.description,
            f"{it.qty:.2f}",
            _money(it.unit_price, inv.currency),
            _money(total, inv.currency),
        ])

    t = Table(data, colWidths=[15 * mm, None, 20 * mm, 30 * mm, 30 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e8f0fb")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#0f172a")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (2,1), (-1,-1), "RIGHT"),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.HexColor("#dbe3ef")),
        ("BOX", (0,0), (-1,-1), 0.25, colors.HexColor("#c9d4e5")),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("BOTTOMPADDING", (0,0), (-1,0), 6),
        ("TOPPADDING", (0,1), (-1,-1), 4),
        ("BOTTOMPADDING", (0,1), (-1,-1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    totals = [
        ["Subtotal:", _money(inv.subtotal, inv.currency)],
        [f"Tax ({inv.tax_rate:.2f}%):", _money(inv.tax_amount, inv.currency)],
        ["Grand Total:", _money(inv.total, inv.currency)],
    ]
    t_tot = Table(totals, colWidths=[None, 40 * mm], hAlign="RIGHT")
    t_tot.setStyle(TableStyle([
        ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ("FONTNAME", (0,0), (-1,-2), "Helvetica"),
        ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
    ]))
    story.append(t_tot)
    story.append(Spacer(1, 14))

    story.append(Paragraph("<b>Authorized</b> — Management", P))

    doc.build(story)
    buf.seek(0)
    return buf.read()


def _render_pdf_via_weasyprint(request, inv) -> bytes | None:
    try:
        from weasyprint import HTML
    except Exception:
        return None

    try:
        html = _render_pdf_html(request, inv)
        pdf_io = BytesIO()
        HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf(pdf_io)
        return pdf_io.getvalue()
    except Exception:
        return None


def _render_pdf_via_playwright(request, inv) -> bytes | None:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None

    html = _render_pdf_html(request, inv)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            page.set_content(html, wait_until="networkidle")
            pdf_bytes = page.pdf(
                format="A4",
                margin={"top": "18mm", "right": "18mm", "bottom": "18mm", "left": "18mm"},
                print_background=True,
            )
            context.close()
            browser.close()
        return pdf_bytes
    except Exception:
        return None


# ---------- PDF endpoints ----------

@login_required
def invoice_pdf(request, pk):
    inv = get_object_or_404(
        Invoice.objects.select_related("user").prefetch_related("items"), pk=pk
    )

    pdf_bytes = _render_pdf_via_playwright(request, inv)
    if pdf_bytes:
        resp = HttpResponse(pdf_bytes, content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="{inv.number}.pdf"'
        resp["X-PDF-Generator"] = "playwright"
        return resp

    pdf_bytes = _render_pdf_via_weasyprint(request, inv)
    if pdf_bytes:
        resp = HttpResponse(pdf_bytes, content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="{inv.number}.pdf"'
        resp["X-PDF-Generator"] = "weasyprint"
        return resp

    pdf_bytes = _reportlab_invoice_pdf(inv)
    messages.info(
        request,
        "Using ReportLab fallback PDF locally (WeasyPrint/Playwright not available).",
    )
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{inv.number}.pdf"'
    resp["X-PDF-Generator"] = "reportlab"
    return resp


# ---------- Email helpers & endpoint ----------

def _email_invoice_to_customer(request, inv) -> bool:
    if not inv.user.email:
        return False

    pdf_bytes = (
        _render_pdf_via_playwright(request, inv)
        or _render_pdf_via_weasyprint(request, inv)
        or _reportlab_invoice_pdf(inv)
    )

    subject = f"Invoice {inv.number}"
    body = render_to_string("invoices/email.txt", {"inv": inv})
    email = EmailMessage(subject, body, to=[inv.user.email])
    email.attach(filename=f"{inv.number}.pdf", content=pdf_bytes, mimetype="application/pdf")
    email.send(fail_silently=False)
    return True


@login_required
@user_passes_test(_is_staff)
def invoice_email(request, pk):
    inv = get_object_or_404(
        Invoice.objects.select_related("user").prefetch_related("items"), pk=pk
    )
    if not inv.user.email:
        messages.error(request, "This customer has no email address.")
        return redirect("invoices:detail", pk=pk)

    _email_invoice_to_customer(request, inv)
    messages.success(request, f"Invoice {inv.number} sent to {inv.user.email}.")
    return redirect("invoices:detail", pk=pk)
