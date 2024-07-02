from django.urls import path

from apps.notification.websocket import consumers

notification_websocket_urlpatterns = [
    path("ws/notification/<str:user_id>", consumers.NotificationConsumer.as_asgi()),
]
