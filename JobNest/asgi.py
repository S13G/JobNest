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

application = get_asgi_application()

# from apps.chat.routing import websocket_urlpatterns
# from apps.chat.socket_auth import TokenAuthMiddleware
#
#
# application = ProtocolTypeRouter(
#     {
#         "http": django_asgi_app,
#         "websocket": TokenAuthMiddleware(URLRouter(websocket_urlpatterns))
#     }
# )
