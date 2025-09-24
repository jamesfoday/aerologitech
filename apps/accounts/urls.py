from django.urls import path
from .views import (
    # End-user
    user_dashboard,
    profile_edit,
    post_login_redirect,
    signup,
    my_messages,
    my_invoices,
    my_receipts,
    my_orders,

    # Staff/admin management
    users_list,
    user_detail,
    user_orders,
    add_user,
    delete_user,
    deactivate_user,
    reactivate_user,
)

app_name = "accounts"

urlpatterns = [
    # End-user routes
    path("dashboard/", user_dashboard, name="dashboard"),
    path("profile/edit/", profile_edit, name="profile_edit"),
    path("route-after-login/", post_login_redirect, name="post_login"),
    path("signup/", signup, name="signup"),

    # “My …” user-scoped shortcuts used by the dashboard buttons
    path("me/messages/", my_messages, name="my_messages"),
    path("me/invoices/", my_invoices, name="my_invoices"),
    path("me/receipts/", my_receipts, name="my_receipts"),
    path("me/orders/", my_orders, name="my_orders"),

    # Staff/admin management
    path("", users_list, name="list"),
    path("<int:pk>/", user_detail, name="detail"),
    path("<int:pk>/orders/", user_orders, name="orders"),
    path("add/", add_user, name="add"),
    path("<int:pk>/deactivate/", deactivate_user, name="deactivate"),
    path("<int:pk>/reactivate/", reactivate_user, name="reactivate"),
    path("<int:pk>/delete/", delete_user, name="delete"),
]
