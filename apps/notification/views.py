from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
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
        description=(
                """This endpoint allows an authenticated user to retrieve all their notifications
            
                ```AVAILABLE_NOTIFICATION_TYPES: PROFILE_UPDATED, COMPLETE_PROFILE, APPLICATION_SCHEDULED_FOR_INTERVIEW, 
                JOB_APPLIED, NEW_JOB_AVAILABLE, APPLICATION_ACCEPTED, APPLICATION_REJECTED``` 
                """
        ),
        tags=['Notification'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Successfully retrieved all notifications",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved all notifications",
                            "data": [
                                {
                                    "id": "81bb123b3-0169-4241-a4de-627699f81217",
                                    "notification_type": "PROFILE_UPDATED",
                                    "message": "Profile updated successfully"
                                },
                                {
                                    "id": "8912186c-72fa-4838-a362-522346a64909",
                                    "notification_type": "COMPLETE_PROFILE",
                                    "message": "Complete your profile"
                                }
                            ]
                        },
                    )
                ]
            )
        }
    )
    def get(self, request):
        user = self.request.user
        notifications = Notification.objects.filter(user=user)

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
