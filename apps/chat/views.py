from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.chat.docs.docs import *
from apps.chat.filters import ChatFilter
from apps.chat.selectors import *
from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.responses import CustomResponse

User = get_user_model()


# Create your views here


class RetrieveChatListView(APIView):
    permission_classes = (IsAuthenticated,)
    filterset_class = ChatFilter
    filter_backends = [DjangoFilterBackend]

    @retrieve_chat_list_docs()
    def get(self, request):
        user = request.user
        queryset = Message.objects.select_related("sender", "receiver").filter(
            Q(sender=user) | Q(receiver=user)).exclude(
            archived_by_users__user=user
        )

        messages = self.filterset_class(data=request.GET, queryset=queryset).qs

        data = retrieve_chat_list_data(messages=messages, current_user=user)
        return CustomResponse.success(message="Returned all list of rooms", data=data)


class RetrieveChatView(APIView):
    permission_classes = (IsAuthenticated,)

    @retrieve_chat_docs()
    def get(self, request, *args, **kwargs):
        friend_id = kwargs.get("friend_id")

        friend = get_friend_by_id(friend_id=friend_id)

        user = request.user

        messages = (
            Message.objects.filter(Q(sender=user) | Q(receiver=user), Q(sender=friend) | Q(receiver=friend))
            .select_related("sender", "receiver").exclude(
                archived_by_users__user=user
            ).order_by("created")
        )
        messages.filter(sender=user).update(is_read=True)

        data = retrieve_chat_data(messages=messages)
        return CustomResponse.success(message="Returned specific chat", data=data)


class ArchiveChatView(APIView):
    permission_classes = (IsAuthenticated,)

    @archive_chat_docs()
    def get(self, request, *args, **kwargs):
        friend_id = kwargs.get("friend_id")

        archive_chat(friend_id=friend_id, current_user=request.user)

        return CustomResponse.success(message="Archived specific chat")


class RemoveArchivedChatView(APIView):
    permission_classes = (IsAuthenticated,)

    @remove_archived_chat_docs()
    def get(self, request, *args, **kwargs):
        user = request.user
        friend_id = kwargs.get("friend_id")

        try:
            archived_messages = ArchivedMessage.objects.filter(
                user=user,
                message__sender_id=friend_id
            ) | ArchivedMessage.objects.filter(
                user=user,
                message__receiver_id=friend_id
            )
            archived_messages.delete()
        except Message.DoesNotExist:
            return RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Chat does not exist",
                                status_code=status.HTTP_400_BAD_REQUEST)

        return CustomResponse.success(message="Unarchived specific chat")


class RetrieveArchivedChatsView(APIView):
    permission_classes = (IsAuthenticated,)

    @retrieve_archive_chats_docs()
    def get(self, request):
        user = request.user
        archived_messages = ArchivedMessage.objects.filter(user=user).select_related('message', 'user')

        data = retrieve_archive_chat_list(messages=archived_messages, current_user=user)
        return CustomResponse.success(message="Returned all list of rooms", data=data)
