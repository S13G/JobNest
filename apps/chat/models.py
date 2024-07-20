from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import UniqueConstraint

from apps.common.models import BaseModel

User = get_user_model()


# Create your models here.

class Message(BaseModel):
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="sender_messages")
    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="receiver_messages")
    text = models.TextField(null=True, blank=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message by {self.sender.email} to {self.receiver.email} : {self.text}"


class ArchivedMessage(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="archived_messages")
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="archived_by_users")

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user', 'message'], name='unique_user_message'
            )
        ]

    def __str__(self):
        return f"Message {self.message.id} archived by {self.user.email}"
