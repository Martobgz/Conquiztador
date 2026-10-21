import random

from django.db import transaction

from .models import Game, Player, WaitingRoomEntry

UNFINISHED_STATUSES = (Game.STATUS_WAITING, Game.STATUS_ACTIVE)
COLORS = (Player.COLOR_RED, Player.COLOR_GREEN, Player.COLOR_BLUE)


class AlreadyWaiting(Exception):
    pass


class AlreadyInGame(Exception):
    pass


def busy_user_ids():
    return Player.objects.filter(game__status__in=UNFINISHED_STATUSES).values("user_id")


def join(user):
    with transaction.atomic():
        if busy_user_ids().filter(user_id=user.pk).exists():
            raise AlreadyInGame
        _, created = WaitingRoomEntry.objects.get_or_create(user=user)
        if not created:
            raise AlreadyWaiting

    form_game()


def leave(user):
    WaitingRoomEntry.objects.filter(user=user).delete()


@transaction.atomic
def form_game():
    eligible = list(WaitingRoomEntry.objects.exclude(user_id__in=busy_user_ids()))
    if len(eligible) < Game.PLAYERS_PER_GAME:
        return None

    chosen = random.sample(eligible, Game.PLAYERS_PER_GAME)
    game = Game.objects.create()
    for entry, color in zip(chosen, COLORS):
        game.add_player(entry.user, color)
    WaitingRoomEntry.objects.filter(pk__in=[entry.pk for entry in chosen]).delete()
    return game
