from django.urls import path

from . import views

app_name = "games"

urlpatterns = [
    path("join/", views.JoinWaitingRoomView.as_view(), name="waiting-room-join"),
    path("leave/", views.LeaveWaitingRoomView.as_view(), name="waiting-room-leave"),
]
