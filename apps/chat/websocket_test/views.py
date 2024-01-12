from django.shortcuts import render


def index(request):
    return render(request, "../apps/chat/websocket_test/templates/index.html")


def room(request, room_name):
    return render(request, "../apps/chat/websocket_test/templates/room.html", {"room_name": room_name})
