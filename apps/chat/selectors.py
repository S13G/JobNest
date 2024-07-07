from django.contrib.auth import get_user_model
from django.db.models import Case, CharField, When, F, QuerySet, Q
from rest_framework import status

from apps.chat.models import Message, ArchivedMessage
from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError

User = get_user_model()


def retrieve_chat_list_data(messages: QuerySet, current_user: User) -> dict:
    # Annotate each message with the 'other' field to identify the friend (either sender or receiver) who is not the current user
    inbox_list = (
        messages.annotate(
            other=Case(
                When(sender=current_user, then=F("receiver")),
                # If the current user is the sender, 'other' is the receiver
                default=F("sender"),  # Otherwise, 'other' is the sender
                output_field=CharField(),
            )
        )
        .order_by("other", "-created")  # Order messages by 'other' and then by creation time (latest first)
        .distinct("other")
    )

    # Sort the inbox list by creation time in descending order
    sorted_inbox_list = sorted(inbox_list, key=lambda x: x.created, reverse=True)

    data = {
        "inbox_list": [
            {
                "id": inbox.id,
                "friend": inbox.receiver if inbox.sender == current_user else inbox.sender,
                "friend_id": str(inbox.receiver.id) if inbox.sender == current_user else str(inbox.sender.id),
                "friend_name": "",
                "friend_profile_image": "",
                "last_message": inbox.text,
                "time": inbox.created
            }
            for inbox in sorted_inbox_list
        ],
        "unread_count": Message.objects.select_related("sender", "receiver")
        .filter(receiver=current_user, is_read=False).count(),
    }

    # Adjust sender details based on the type of authenticated user
    for inbox in data["inbox_list"]:
        friend = inbox["friend"]
        if hasattr(friend, "employee_profile"):
            inbox["friend_name"] = friend.employee_profile.full_name
            inbox["friend_profile_image"] = friend.profile_image_url
        elif hasattr(friend, "company_profile"):
            inbox["friend_name"] = friend.company_profile.name
            inbox["friend_profile_image"] = friend.profile_image_url

        del inbox["friend"]

    return data


def get_friend_by_id(friend_id: str) -> User | RequestError:
    friend = User.objects.get_or_none(id=friend_id)

    if friend is None:
        return RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Friend does not exist",
                            status_code=status.HTTP_400_BAD_REQUEST)
    return friend


def retrieve_chat_data(messages: QuerySet) -> dict:
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

    return data


def archive_chat(friend_id: str, current_user: User) -> RequestError:
    try:
        messages = Message.objects.filter(
            Q(sender=current_user, receiver_id=friend_id) |
            Q(sender_id=friend_id, receiver=current_user))

        archived_messages = [
            ArchivedMessage(user=current_user, message=message)
            for message in messages
        ]

        ArchivedMessage.objects.bulk_create(archived_messages, ignore_conflicts=True)

    except Message.DoesNotExist:
        return RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Chat does not exist",
                            status_code=status.HTTP_400_BAD_REQUEST)


def retrieve_archive_chat_list(messages: QuerySet, current_user: User) -> dict:
    inbox_list = (
        messages.annotate(
            other=Case(
                When(message__sender=current_user, then=F("message__receiver")),
                default=F("message__sender"),
                output_field=CharField(),
            )
        )
        .order_by("other", "-message__created")
        .distinct("other")
    )

    sorted_inbox_list = sorted(inbox_list, key=lambda x: x.message.created, reverse=True)

    data = {
        "inbox_list": [
            {
                "id": inbox.message.id,
                "friend": inbox.message.receiver if inbox.message.sender == current_user else inbox.message.sender,
                "friend_id": str(inbox.message.receiver.id) if inbox.message.sender == current_user else str(
                    inbox.message.sender.id),
                "friend_name": "",
                "friend_profile_image": "",
                "last_message": inbox.message.text,
                "time": inbox.message.created
            }
            for inbox in sorted_inbox_list
        ],
        "unread_count": Message.objects.filter(receiver=current_user, is_read=False).count(),
    }

    for inbox in data["inbox_list"]:
        friend = inbox["friend"]
        if hasattr(friend, "employee_profile"):
            inbox["friend_name"] = friend.employee_profile.full_name
            inbox["friend_profile_image"] = friend.profile_image_url
        elif hasattr(friend, "company_profile"):
            inbox["friend_name"] = friend.company_profile.name
            inbox["friend_profile_image"] = friend.profile_image_url

        del inbox["friend"]

    return data
