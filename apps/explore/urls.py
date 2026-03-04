from django.urls import path

from . import views

app_name = "explore"

urlpatterns = [
    path("gambia/", views.gambia_page, name="gambia_page"),
    path("gambia/nearby/", views.nearby, name="nearby"),
    path("gambia/place/<slug:slug>/", views.place_detail, name="place_detail"),
]
