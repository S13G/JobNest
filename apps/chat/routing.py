from django.urls import path

from apps.chat import consumers

websocket_urlpatterns = [
    path(r"ws/chat/<str:id>", consumers.ChatConsumer.as_asgi()),
]
