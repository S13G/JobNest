from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.db import models

from apps.common.models import BaseModel

User = get_user_model()


# Create your models here.
class Notification(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Notification by {self.user.email} : {self.text}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            str(self.user.id),
            {
                "type": "notification_message",
                "notification": {
                    'message': self.message
                }
            }
        )
