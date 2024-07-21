from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.common.responses import CustomResponse
from apps.notification.docs.docs import notification_docs
from apps.notification.models import Notification


# Create your views here.

class RetrieveAllNotificationsView(APIView):
    permission_classes = (IsAuthenticated,)

    @method_decorator(cache_page(60 * 15, key_prefix="all_notifications"))
    @notification_docs()
    def get(self, request):
        user = request.user
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
        return CustomResponse.success(message="Successfully retrieved all notifications", data=data)
