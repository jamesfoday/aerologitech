from django.urls import path
from .views import invoice_list, invoice_detail, invoice_create, invoice_update, invoice_delete, invoice_pdf, invoice_email

app_name = "invoices"

urlpatterns = [
    path("", invoice_list, name="list"),
    path("<int:pk>/", invoice_detail, name="detail"),
    path("create/", invoice_create, name="create"),
    path("<int:pk>/edit/", invoice_update, name="update"),
    path("<int:pk>/delete/", invoice_delete, name="delete"),  # <-- new
    path("<int:pk>/pdf/", invoice_pdf, name="pdf"),
    path("<int:pk>/email/", invoice_email, name="email"),
]
