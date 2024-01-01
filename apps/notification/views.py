from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.responses import CustomResponse
from apps.notification.models import Notification


# Create your views here.

class RetrieveAllNotificationsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Retrieve all notifications",
        description="This endpoint allows a user to retrieve all notifications",
        tags=['Notification'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved all notifications",
            )
        }
    )
    def get(self, request):
        user = self.request.user
        notifications = Notification.objects.filter(user=user)
        data = [
            {
                "id": single_notification.id,
                "notification_type": single_notification.notification_type,
                "message": single_notification.message
            }
            for single_notification in notifications
        ]
        return CustomResponse.success(message="Successfully retrieved all notifications", data=data)
