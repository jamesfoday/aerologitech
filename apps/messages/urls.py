from django.urls import path
from .views import messages_list, thread_view, send_message

app_name = "messages"

urlpatterns = [
    path("", messages_list, name="list"),
    path("<int:user_id>/", thread_view, name="thread"),
    path("<int:user_id>/send/", send_message, name="send"),
]
