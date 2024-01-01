from django.contrib.auth import get_user_model
from django.db import models

from apps.common.models import BaseModel

User = get_user_model()


# Create your models here.

class Message(BaseModel):
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="sender_messages")
    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="receiver_messages")
    text = models.TextField(null=True, blank=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message by {self.sender.first_name} to {self.receiver.first_name} : {self.text}"
