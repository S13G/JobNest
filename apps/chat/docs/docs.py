from drf_spectacular.utils import OpenApiTypes, OpenApiResponse, OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status


def retrieve_chat_list_docs():
    return extend_schema(
        summary="Retrieve and filter chat list",
        description=
        """
        This endpoint allows a user to retrieve and filter their chat list based on read status. 
        Users can specify if they want to filter the chat list to show only read or unread messages 
        by using the `is_read` query parameter. The response includes a list of chat rooms, each with 
        details about the last message, the friend's information, and the timestamp of the last message.
        Additionally, it provides the count of unread messages.
        """,
        tags=['Chat'],
        parameters=[
            OpenApiParameter(name='is_read', type=OpenApiTypes.BOOL,
                             description="Filter chat list by read status (true for read, false for unread)"),
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Returned list of chat rooms with optional filtering by read status",
                examples=[
                    OpenApiExample(
                        name="Retrieve chat list",
                        value={
                            "status": "success",
                            "message": "Returned all list of rooms",
                            "data": {
                                "inbox_list": [
                                    {
                                        "id": "d62f585a-42e6-4c97-ad17-b7331dc9286f",
                                        "friend_id": "cbc4953f-2379-4439-9bf9-26bc246ec19f",
                                        "friend_name": "Google",
                                        "friend_profile_image": "/media/static/user_avatars/Screenshot_from_2024-07-01_06-53-03.png",
                                        "last_message": "I am good and you?",
                                        "time": "2024-07-07T21:39:21.534895Z"
                                    }
                                ],
                                "unread_count": 1
                            }
                        }
                    )
                ]
            ),
        }
    )


def retrieve_chat_docs():
    return extend_schema(
        summary="Retrieve a specific chat",
        description=
        """
        Retrieve specific chat
        """,
        tags=['Chat'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Return specific chat",
                examples=[
                    OpenApiExample(
                        name="Retrieve chat",
                        value={
                            "status": "success",
                            "message": "Returned specific chat",
                            "data": {
                                "messages": [
                                    {
                                        "id": "60405639-3e5d-436b-a759-2c5b684262f6",
                                        "sender_name": "Capone Richie",
                                        "sender_profile_image": "/media/static/user_avatars/Screenshot.png",
                                        "friend_name": "Google",
                                        "friend_profile_image": "/media/static/user_avatars/Screenshot.png",
                                        "text": "hi",
                                        "is_read": True
                                    },
                                    {
                                        "id": "d62f585a-42e6-4c97-ad17-b7331dc9286f",
                                        "sender_name": "Google",
                                        "sender_profile_image": "/media/static/user_avatars/Screenshot.png",
                                        "friend_name": "Capone Richie",
                                        "friend_profile_image": "/media/static/user_avatars/Screenshot.png",
                                        "text": "i am good and you",
                                        "is_read": False
                                    }
                                ]
                            }
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="Friend does not exist",
                examples=[
                    OpenApiExample(
                        name="Friend does not exist",
                        value={
                            "status": "error",
                            "message": "Friend does not exist",
                            "code": "non_existent",
                        }
                    )
                ]
            )
        }
    )


def archive_chat_docs():
    return extend_schema(
        summary="Archive a specific chat",
        description=
        """
        This endpoint allows a user to retrieve the chat history with a specific friend. 
        The response includes a list of messages exchanged between the user and the specified friend, 
        along with details such as the sender's name, profile image, message text, and read status.
        If the friend does not exist, a 404 error is returned.
        """,
        tags=['Chat'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Archived specific chat",
                examples=[
                    OpenApiExample(
                        name="Archive chat",
                        value={
                            "status": "success",
                            "message": "Archived specific chat",
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="Chat does not exist",
                examples=[
                    OpenApiExample(
                        name="Chat does not exist",
                        value={
                            "status": "error",
                            "message": "Chat does not exist",
                            "code": "non_existent",
                        }
                    )
                ]
            )
        }
    )


def remove_archived_chat_docs():
    return extend_schema(
        summary="Remove a specific chat from archived",
        description=
        """
        This endpoint allows a user to remove a specific chat from their archived list. 
        To successfully unarchive a chat, the user must specify the friend's ID. 
        The response confirms the chat has been unarchived.
        """,
        tags=['Chat'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Unarchived specific chat",
                examples=[
                    OpenApiExample(
                        name="Unarchive chat",
                        value={
                            "status": "success",
                            "message": "Unarchived specific chat",
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="Chat does not exist",
                examples=[
                    OpenApiExample(
                        name="Chat does not exist",
                        value={
                            "status": "error",
                            "message": "Chat does not exist",
                            "code": "non_existent",
                        }
                    )
                ]
            )
        }
    )


def retrieve_archive_chats_docs():
    return extend_schema(
        summary="Retrieve archived chat list",
        description=
        """
        This endpoint allows a user to retrieve their archived chat list. 
        Archived chats are those that have been moved out of the active inbox 
        but can be accessed again through this endpoint. The response includes 
        details such as the friend's name, profile image, the last message exchanged, 
        and the timestamp of the last message. Additionally, it provides the count 
        of unread messages in archived chats.
        """,
        tags=['Chat'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Returned all list of rooms",
                examples=[
                    OpenApiExample(
                        name="Retrieve archive chat list",
                        value={
                            "status": "success",
                            "message": "Returned all list of rooms",
                            "data": {
                                "inbox_list": [
                                    {
                                        "id": "d62f585a-42e6-4c97-ad17-b7331dc9286f",
                                        "friend_id": "cbc4953f-2379-4439-9bf9-26bc246ec19f",
                                        "friend_name": "Google",
                                        "friend_profile_image": "/media/static/user_avatars/Screenshot_from_2024-07-01_06-53-03.png",
                                        "last_message": "i am good and you",
                                        "time": "2024-07-07T21:39:21.534895Z"
                                    }
                                ],
                                "unread_count": 1
                            }
                        }
                    )
                ]
            ),
        }
    )
