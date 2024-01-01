from django.urls import re_path, path

from apps.chat import consumers

websocket_urlpatterns = [
    path(r"ws/chat/<str:id>", consumers.ChatConsumer.as_asgi()),
    path("ws/notification/<str:user_id>", consumers.NotificationConsumer.as_asgi()),
]
