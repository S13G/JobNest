from django.shortcuts import render


def index(request):
    return render(request, "../apps/chat/tests/templates/index.html")


def room(request, room_name):
    return render(request, "../apps/chat/tests/templates/room.html", {"room_name": room_name})
