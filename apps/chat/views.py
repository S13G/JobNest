from django.contrib.auth import get_user_model
from django.db.models import Q, Case, When, F, CharField
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.chat.filters import ChatFilter
from apps.chat.models import Message
from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.responses import CustomResponse

User = get_user_model()


# Create your views here


class RetrieveChatListView(APIView):
    permission_classes = (IsAuthenticated,)
    filterset_class = ChatFilter
    filter_backends = [DjangoFilterBackend]

    @extend_schema(
        summary="Retrieve and filter chat list",
        description="This endpoint allows a user to retrieve and filter chat list",
        tags=['Chat'],
        parameters=[
            OpenApiParameter(name='is_read', type=OpenApiTypes.BOOL, description="Check read status", required=False),
            OpenApiParameter(name='is_archived', type=OpenApiTypes.BOOL, description="Check archived status",
                             required=False),
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Returned all list of rooms",
            ),
        }
    )
    def get(self, request):
        user = request.user
        queryset = Message.objects.select_related("sender", "receiver").filter(Q(sender=user) | Q(receiver=user))
        messages = self.filterset_class(data=request.GET, queryset=queryset).qs

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
                    "sender": inbox.sender,
                    "friend": inbox.receiver,
                    "friend_name": "",
                    "friend_profile_image": inbox.receiver.profile_image_url,
                    "last_message": inbox.text,
                    "time": inbox.created
                }
                for inbox in sorted_inbox_list
            ],
            "unread_count": Message.objects.select_related("sender", "receiver")
            .filter(receiver=user, is_read=False).count(),
        }

        # Adjust sender details based on the type of authenticated user
        for inbox in data["inbox_list"]:
            if hasattr(inbox['friend'], "employee_profile"):
                inbox["friend_name"] = inbox["friend"].employee_profile.full_name
            elif hasattr(inbox['friend'], "company_profile"):
                inbox["friend_name"] = inbox["friend"].company_profile.name

            del inbox["friend"]
            del inbox["sender"]
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
                    "sender": message.sender,
                    "sender_name": "",
                    "sender_profile_image": message.sender.profile_image_url,
                    "friend": message.receiver,
                    "friend_name": "",
                    "friend_profile_image": message.receiver.profile_image_url,
                    "text": message.text,
                    "is_read": message.is_read
                }
                for message in messages
            ]
        }

        # Adjust receiver details based on the type of authenticated user
        for message in data["messages"]:
            sender = message["sender"]
            if hasattr(sender, "employee_profile"):
                message["sender_name"] = sender.employee_profile.full_name
            elif hasattr(sender, "company_profile"):
                message["sender_name"] = sender.company_profile.name
            del message["sender"]

            friend = message["friend"]
            if hasattr(friend, "employee_profile"):
                message["friend_name"] = friend.employee_profile.full_name
            elif hasattr(friend, "company_profile"):
                message["friend_name"] = friend.company_profile.name
            del message["friend"]

        return CustomResponse.success(message="Returned specific chat", data=data)


class ArchiveChatView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Archive a specific chat",
        description="Archive specific chat: Make sure you specify the friend id",
        tags=['Chat'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Archived specific chat",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid friend id",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Chat does not exist",
            )
        }
    )
    def get(self, request, *args, **kwargs):
        friend_id = self.kwargs.get("friend_id")
        if not friend_id:
            raise RequestError(err_code=ErrorCode.INVALID_ENTRY, err_msg="Invalid friend id",
                               status_code=status.HTTP_400_BAD_REQUEST)

        try:
            Message.objects.filter(
                Q(sender=request.user, receiver_id=friend_id) |
                Q(sender_id=friend_id, receiver=request.user)).update(is_archived=True)
        except Message.DoesNotExist:
            return RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Chat does not exist",
                                status_code=status.HTTP_400_BAD_REQUEST)

        return CustomResponse.success(message="Archived specific chat")


class RemoveArchivedChatView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Removes a specific chat from archived",
        description="Removes a specific chat from the archived list: Make sure you specify the friend id",
        tags=['Chat'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Unarchived specific chat",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid friend id",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Chat does not exist",
            )
        }
    )
    def get(self, request, *args, **kwargs):
        friend_id = self.kwargs.get("friend_id")
        if not friend_id:
            raise RequestError(err_code=ErrorCode.INVALID_ENTRY, err_msg="Invalid friend id",
                               status_code=status.HTTP_400_BAD_REQUEST)

        try:
            Message.objects.filter(sender=request.user, receiver_id=friend_id).update(is_archived=False)
        except Message.DoesNotExist:
            return RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Chat does not exist",
                                status_code=status.HTTP_400_BAD_REQUEST)

        return CustomResponse.success(message="Unarchived specific chat")
