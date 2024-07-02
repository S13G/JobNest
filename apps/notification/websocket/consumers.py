import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.room_name = f"notification_{self.user_id}"
        self.room_group_name = f"notification_{self.user_id}"

        # Check if the user is authenticated.
        if self.scope['user'].is_authenticated and (str(self.scope['user'].id) == str(self.user_id)):
            # Add the connection to the wager group for broadcasting messages.
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
        else:
            # User is not authenticated, close the connection.
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def notification_message(self, event):
        message = event['notification']['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
