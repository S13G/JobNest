from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.responses import CustomResponse
from apps.notification.docs.docs import notification_docs
from apps.notification.models import Notification


# Create your views here.

class RetrieveAllNotificationsView(APIView):
    permission_classes = (IsAuthenticated,)

    @notification_docs()
    def get(self, request):
        user = request.user

        # Set cache key
        cache_key = f"all_notifications_{user.id}"
        cached_data = cache.get(cache_key)

        # Retrieve data from cache if it exists
        if cached_data:
            return CustomResponse.success(message="Successfully retrieved all notifications", data=cached_data)

        # Get all notifications
        notifications = Notification.objects.select_related("user").filter(user=user)

        # Create a list of dictionaries containing notification details
        data = [
            {
                "id": single_notification.id,
                "notification_type": single_notification.notification_type,
                "message": single_notification.message
            }
            for single_notification in notifications
        ]

        # Cache the data
        cache.set(cache_key, data, 60 * 60)
        return CustomResponse.success(message="Successfully retrieved all notifications", data=data)
