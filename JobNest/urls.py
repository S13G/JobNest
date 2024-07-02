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
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

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
    path('__debug__/', include('debug_toolbar.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
