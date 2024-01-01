import json

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from apps.chat.models import Message
from apps.chat.serializers import MessageSerializer
from apps.common.consumers import BaseConsumer
from apps.common.errors import ErrorCode

User = get_user_model()


class ChatConsumer(BaseConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["id"]
        self.room_group_name = f"chat_{self.room_name}"

        user = await self.get_authenticated_user()
        if not user:
            await self.close(code=4003)

        await self.accept()

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Mark all unread messages as read
        await self.mark_messages_as_read(user=user)

    # Checking if the user is authenticated
    async def get_authenticated_user(self):
        if self.scope["user"].is_authenticated:
            return self.scope["user"]
        return None

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        try:
            # Extract and validate the message text
            serializer = MessageSerializer(data=json.loads(text_data))
            serializer.is_valid(raise_exception=True)
            data = serializer.data['text']

            # Perform message sending logic from SendMessageView
            await self.send_message(message_text=data)

        except Exception as e:
            # Handle errors and send appropriate response
            await self.send(text_data=json.dumps({"error": str(e)}))

    async def send_message(self, message_text):

        message_data = await self.message_data(message=message_text)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat_message", "message": message_data},
        )

    async def chat_message(self, event):
        # Send message to websocket
        await self.send(text_data=json.dumps(event["message"]))

    @database_sync_to_async
    def mark_messages_as_read(self, user):
        try:
            friend = User.objects.get(id=self.room_name)
        except Exception as e:
            return self.send_error_message(
                {"type": ErrorCode.NON_EXISTENT, "message": "Friend does not exist: " + str(e)}
            )

        # Mark all unread messages as read
        Message.objects.filter(receiver=user, sender=friend, is_read=False).update(is_read=True)

    @database_sync_to_async
    def message_data(self, message):
        try:
            friend = User.objects.get(id=self.room_name)
        except Exception as e:
            return self.send_error_message(
                {"type": ErrorCode.NON_EXISTENT, "message": "Friend does not exist: " + str(e)}
            )

        user = self.scope["user"]

        # Create message
        created_message = Message.objects.create(sender=user, receiver=friend, text=message)

        # Prepare message data
        message_data = {
            "id": str(created_message.id),
            "sender_id": str(created_message.sender.id),
            "sender_profile_image": created_message.sender.profile_image(),
            "receiver_id": str(created_message.receiver.id),
            "receiver_profile_image": created_message.receiver.profile_image(),
            "text": created_message.text,
            "is_read": created_message.is_read,
            "time12": created_message.created.strftime("%I:%M %p"),
            "time24": created_message.created.strftime("%H:%M"),
            "receiver_unread": Message.objects.filter(sender=user, receiver=friend, is_read=False).count(),
        }

        return message_data
