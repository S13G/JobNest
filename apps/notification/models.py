from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.db import models

from apps.common.models import BaseModel
from apps.notification.choices import NOTIFICATION_TYPE
from utilities.cache_clear import clear_cache

User = get_user_model()


# Create your models here.
class Notification(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=255, choices=NOTIFICATION_TYPE)
    message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Notification by {self.user.email} : {self.message}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        channel_layer = get_channel_layer()  # Get the channel layer
        async_to_sync(channel_layer.group_send)(
            f"notification_{self.user.id}",  # Group name based on user ID
            {
                "type": "notification_message",  # This type must match the method in your consumer
                "notification": {  # Payload of the message
                    'message': self.message
                }
            }
        )

        # Clear cache
        clear_cache(cache_key_prefix="all_notifications")
