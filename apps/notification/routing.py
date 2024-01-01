from django.urls import re_path, path

from apps.notification import consumers

notification_websocket_urlpatterns = [
    path("ws/notification/<str:user_id>", consumers.NotificationConsumer.as_asgi()),
]
