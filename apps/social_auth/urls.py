from django.urls import path

from apps.social_auth.views import GoogleSocialAuthView

urlpatterns = [
    path('google-auth', GoogleSocialAuthView.as_view(), name="google-auth"),
]
