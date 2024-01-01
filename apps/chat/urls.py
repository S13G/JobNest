from django.urls import path

from apps.chat.views import *

urlpatterns = [
    path("messages/all", RetrieveChatListView.as_view(), name="retrieve-chat-list"),
    path("messages/<str:friend_id>", RetrieveChatView.as_view(), name="retrieve-chat"),
    path("messages/<str:friend_id>/read-status", UpdateMessagesReadStatus.as_view(),
         name="update-messages-read-status"),
]
