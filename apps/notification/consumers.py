import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.room_name = f"notification_{user_id}"
        self.room_group_name = f"notification_{user_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def notification_message(self, event):
        await self.send(text_data=json.dumps({'message': event['message']}))
