from django.urls import path

from apps.notification.views import *

urlpatterns = [
    path('all/', RetrieveAllNotificationsView.as_view(), name="retrieve-all-notifications"),
]
