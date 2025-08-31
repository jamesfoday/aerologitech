from django.urls import path
from .views import users_list, user_detail

app_name = "accounts"

urlpatterns = [
    path("", users_list, name="list"),
    path("<int:pk>/", user_detail, name="detail"),
]
