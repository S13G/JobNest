"""
ASGI config for JobNest project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'JobNest.settings')

django_asgi_app = get_asgi_application()

from apps.chat.websocket.routing import websocket_urlpatterns
from apps.notification.websocket.routing import notification_websocket_urlpatterns
from apps.common.socket.socket_auth import JwtAuthMiddlewareStack

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JwtAuthMiddlewareStack(
            inner=URLRouter(websocket_urlpatterns + notification_websocket_urlpatterns),
        ),
    }
)
