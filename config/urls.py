from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.views import home, home_about

urlpatterns = [
    path('admin/', admin.site.urls),

    # Public
    path('', home, name='home'),
    path('about/', home_about, name='about'),

    # Apps
    path("dashboard/", include("apps.dashboard.urls")),
    path("users/", include("apps.accounts.urls", namespace="accounts")),
    path("orders/", include("apps.orders.urls", namespace="orders")),
    path("messages/", include("apps.messages.urls", namespace="messages")),
    path("invoices/", include("apps.invoices.urls")),
    path("services/", include(("apps.services.urls", "services"), namespace="services")),

    # Auth
    path("accounts/", include("django.contrib.auth.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
