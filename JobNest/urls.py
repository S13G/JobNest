"""
URL configuration for JobNest project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.views import APIView

from apps.common.responses import CustomResponse


class HealthCheckView(APIView):
    @extend_schema(
        "/",
        summary="API Health Check",
        description="This endpoint checks the health of the API",
        tags=["Health Check"],
    )
    async def get(self, request):
        return CustomResponse.success(message="pong")


def handler404(request, exception=None):
    response = JsonResponse({"status": "failure", "message": "Not Found"})
    response.status_code = 404
    return response


def handler500(request, exception=None):
    response = JsonResponse({"status": "failure", "message": "Server Error"})
    response.status_code = 500
    return response


handler404 = handler404
handler500 = handler500

# Version 1 URLs
urlpatterns_v1 = [
    path("auth/", include("apps.core.urls")),
    path("social_auth/", include("apps.social_auth.urls")),
    path("misc/", include("apps.misc.urls")),
    path("jobs/", include("apps.jobs.urls")),
    path("chat/", include("apps.chat.urls")),
    path("notification/", include("apps.notification.urls")),
]

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path('admin/', admin.site.urls),
    path("api/v1/", include(urlpatterns_v1)),
    path("api/v1/healthcheck/", HealthCheckView.as_view()),
    path('__debug__/', include('debug_toolbar.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
