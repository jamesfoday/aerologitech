from django.urls import path
from .views import orders_list, order_detail, order_thanks
from . import views

app_name = "orders"

urlpatterns = [
    path("", orders_list, name="list"),
    path("<int:pk>/", order_detail, name="detail"),
    path("create/", views.order_create, name="create"),
    path("thanks/<int:pk>/", order_thanks, name="thanks"),
]
