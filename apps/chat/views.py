from django.contrib.auth import get_user_model
from django.db.models import Q, Case, When, F, CharField
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiTypes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.chat.models import Message
from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.responses import CustomResponse

User = get_user_model()


# Create your views here


class RetrieveChatListView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Retrieve chat or message list",
        description="List of rooms",
        tags=['Chat'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Returned all list of rooms",
            ),
        }
    )
    def get(self, request):
        user = self.request.user

        messages = Message.objects.select_related("sender", "receiver").filter(Q(sender=user) | Q(receiver=user))

        inbox_list = (
            messages.annotate(
                other=Case(
                    When(sender=user, then=F("receiver")),
                    default=F("sender"),
                    output_field=CharField(),
                )
            )
            .order_by("other", "-created")
            .distinct("other")
        )

        sorted_inbox_list = sorted(inbox_list, key=lambda x: x.created, reverse=True)

        data = {
            "inbox_list": [
                {
                    "id": inbox.id,
                    "receiver_id": inbox.receiver.id,
                    "receiver_name": f"{inbox.receiver.first_name} {inbox.receiver.last_name}",
                    "receiver_profile_image": inbox.receiver.profile_image(),
                    "last_message": inbox.text,
                    "time": inbox.created
                }
                for inbox in sorted_inbox_list
            ],
            "messages": [
                {
                    "id": message.id,
                    "text": message.text,
                    "is_read": message.is_read
                }
                for message in messages
            ]
        }

        return CustomResponse.success(message="Returned all list of rooms", data=data)


class RetrieveChatView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Retrieve a specific chat",
        description="Retrieve specific chat",
        tags=['Chat'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Return specific chat",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid friend id",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Friend does not exist",
            )
        }
    )
    def get(self, request, *args, **kwargs):
        friend_id = self.kwargs.get("friend_id")
        if not friend_id:
            raise RequestError(err_code=ErrorCode.INVALID_ENTRY, err_msg="Invalid friend id",
                               status_code=status.HTTP_400_BAD_REQUEST)

        try:
            friend = User.objects.get(id=friend_id)
        except User.DoesNotExist:
            return RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Friend does not exist",
                                status_code=status.HTTP_400_BAD_REQUEST)

        user = self.request.user

        messages = (
            Message.objects.filter(Q(sender=user) | Q(receiver=user), Q(sender=friend) | Q(receiver=friend))
            .select_related("sender", "receiver")
            .order_by("created")
        )
        messages.filter(sender=user).update(is_read=True)

        data = {
            "messages": [
                {
                    "id": message.id,
                    "sender_id": message.sender.id,
                    "sender_profile_image": message.sender.profile_image(),
                    "receiver_id": message.receiver.id,
                    "receiver_profile_image": message.receiver.profile_image(),
                    "text": message.text,
                    "is_read": message.is_read
                }
                for message in messages
            ]
        }
        return CustomResponse.success(message="Returned specific chat", data=data)


class UpdateMessagesReadStatus(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Change message read status",
        description="Update chat messages read status",
        tags=['Chat'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Success",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid friend id",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Sender does not exist",
            )
        }
    )
    def post(self, request, *args, **kwargs):
        friend_id = self.kwargs.get("friend_id")
        if not friend_id:
            return RequestError(err_code=ErrorCode.INVALID_ENTRY, err_msg="Invalid sender id",
                                status_code=status.HTTP_400_BAD_REQUEST)

        try:
            friend = User.objects.get(id=friend_id)
        except User.DoesNotExist:
            return RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Sender does not exist",
                                status_code=status.HTTP_404_NOT_FOUND)

        user = self.request.user
        Message.objects.filter(sender=friend, receiver=user, is_read=False).update(is_read=True)
        return CustomResponse.success(message="Success")
