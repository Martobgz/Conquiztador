from django.contrib.auth import get_user_model
from django.test import TestCase

from games import waiting_room
from games.models import Game, Player, WaitingRoomEntry

User = get_user_model()


def make_waiting(*usernames):
    users = [
        User.objects.create_user(username=name, email=f"{name}@example.com")
        for name in usernames
    ]
    for user in users:
        WaitingRoomEntry.objects.create(user=user)
    return users


class FormGameTests(TestCase):
    def test_five_waiting_forms_one_game_and_leaves_two(self):
        users = make_waiting("ana", "boris", "vera", "georgi", "dimitar")
        old_game = Game.objects.create()

        game = waiting_room.form_game()

        self.assertIsNotNone(game)
        game.refresh_from_db()
        self.assertEqual(game.status, "waiting")
        self.assertEqual(Game.objects.count(), 2)
        self.assertTrue(Game.objects.filter(pk=old_game.pk).exists())

        players = list(game.players.all())
        self.assertEqual(len(players), 3)
        self.assertEqual(len({player.user_id for player in players}), 3)
        self.assertCountEqual(
            [player.color for player in players], ["red", "green", "blue"]
        )
        self.assertTrue(all(player.score == 0 for player in players))
        self.assertEqual(Player.objects.count(), 3)
        self.assertEqual(game.rounds.count(), 0)

        chosen = {player.user_id for player in players}
        remaining = set(WaitingRoomEntry.objects.values_list("user_id", flat=True))
        self.assertEqual(len(remaining), 2)
        self.assertEqual(chosen | remaining, {user.pk for user in users})
        self.assertFalse(chosen & remaining)

    def test_two_waiting_changes_nothing(self):
        users = make_waiting("ana", "boris")

        game = waiting_room.form_game()

        self.assertIsNone(game)
        self.assertEqual(Game.objects.count(), 0)
        self.assertEqual(Player.objects.count(), 0)
        self.assertCountEqual(
            WaitingRoomEntry.objects.values_list("user_id", flat=True),
            [user.pk for user in users],
        )
