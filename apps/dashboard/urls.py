from django.urls import path
from .views import (
    dashboard_view,
    profile_edit_view,
    places_list_view,
    places_create_view,
    places_edit_view,
    places_delete_view,
)

app_name = "dashboard"

urlpatterns = [
    path("", dashboard_view, name="home"),
    path("profile/edit/", profile_edit_view, name="profile_edit"),
    path("places/", places_list_view, name="places_list"),
    path("places/create/", places_create_view, name="places_create"),
    path("places/<int:pk>/edit/", places_edit_view, name="places_edit"),
    path("places/<int:pk>/delete/", places_delete_view, name="places_delete"),
]
