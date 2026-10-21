from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import waiting_room


class JoinWaitingRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            waiting_room.join(request.user)
        except waiting_room.AlreadyWaiting:
            return Response(
                {"errors": {"detail": ["You are already in the waiting room."]}},
                status=status.HTTP_409_CONFLICT,
            )
        except waiting_room.AlreadyInGame:
            return Response(
                {"errors": {"detail": ["You are already playing in a game."]}},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_201_CREATED)


class LeaveWaitingRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        waiting_room.leave(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
