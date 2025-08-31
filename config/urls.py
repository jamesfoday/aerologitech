from django.contrib import admin
from django.urls import path, include
from apps.core.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path("dashboard/", include("apps.dashboard.urls")),
     path("users/", include("apps.accounts.urls", namespace="accounts")),

]
