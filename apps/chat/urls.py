from django.urls import path

from apps.chat.views import *

urlpatterns = [
    path("messages/all", RetrieveChatListView.as_view(), name="retrieve-chat-list"),
    path("messages/<str:friend_id>", RetrieveChatView.as_view(), name="retrieve-chat"),
]
