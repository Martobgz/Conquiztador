from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from games.models import Game, Player, Round

User = get_user_model()


def make_user(username):
    return User.objects.create_user(username=username, email=f"{username}@example.com")


class GameCreationTests(TestCase):
    def test_new_game_is_waiting(self):
        game = Game.objects.create()

        self.assertEqual(game.status, "waiting")
        self.assertIsNotNone(game.created_at)
        self.assertFalse(game.is_active())
        self.assertFalse(game.is_completed())

    def test_new_game_has_no_players_or_rounds(self):
        game = Game.objects.create()

        self.assertEqual(game.players.count(), 0)
        self.assertIsNone(game.get_current_round())

    def test_new_game_cannot_start_as_active(self):
        with self.assertRaises(ValidationError):
            Game(status="active").full_clean()

    def test_status_must_be_a_known_choice(self):
        game = Game.objects.create()
        game.status = "paused"

        with self.assertRaises(ValidationError):
            game.full_clean()


class GameLifecycleTests(TestCase):
    def setUp(self):
        self.game = Game.objects.create()
        self.users = [make_user(name) for name in ("ana", "boris", "vera")]

    def add_players(self, count=3):
        colors = ("red", "green", "blue")
        for user, color in list(zip(self.users, colors))[:count]:
            self.game.add_player(user, color)

    def test_add_three_players(self):
        self.add_players()

        self.assertEqual(self.game.players.count(), 3)
        self.assertCountEqual(
            self.game.players.values_list("color", flat=True), ["red", "green", "blue"]
        )
        self.assertCountEqual(
            [player.user for player in self.game.players.all()], self.users
        )

    def test_start_with_three_players(self):
        self.add_players()

        self.game.start()

        self.game.refresh_from_db()
        self.assertEqual(self.game.status, "active")
        self.assertTrue(self.game.is_active())

    def test_cannot_start_with_fewer_than_three_players(self):
        self.add_players(count=2)

        with self.assertRaises(ValidationError):
            self.game.start()

        self.assertEqual(self.game.status, "waiting")
        self.game.refresh_from_db()
        self.assertEqual(self.game.status, "waiting")

    def test_cannot_start_twice(self):
        self.add_players()
        self.game.start()

        with self.assertRaises(ValidationError):
            self.game.start()

    def test_fourth_player_cannot_join(self):
        self.add_players()

        with self.assertRaises(ValidationError):
            self.game.add_player(make_user("georgi"), "red")
        self.assertEqual(self.game.players.count(), 3)

    def test_complete_active_game(self):
        self.add_players()
        self.game.start()

        self.game.complete()

        self.game.refresh_from_db()
        self.assertEqual(self.game.status, "completed")
        self.assertTrue(self.game.is_completed())
        self.assertFalse(self.game.is_active())

    def test_waiting_game_cannot_be_completed(self):
        self.add_players()

        with self.assertRaises(ValidationError):
            self.game.complete()
        self.assertEqual(self.game.status, "waiting")

    def test_cannot_complete_game_with_unfinished_round(self):
        self.add_players()
        self.game.start()
        self.game.create_round(Round.TYPE_BATTLE)

        with self.assertRaises(ValidationError):
            self.game.complete()
        self.assertEqual(self.game.status, "active")

    def test_completed_game_cannot_go_back_to_active(self):
        self.add_players()
        self.game.start()
        self.game.complete()
        self.game.status = "active"

        with self.assertRaises(ValidationError):
            self.game.full_clean()

    def test_completed_game_accepts_no_new_rounds(self):
        self.add_players()
        self.game.start()
        self.game.complete()

        with self.assertRaises(ValidationError):
            self.game.create_round(Round.TYPE_BONUS)
        self.assertEqual(self.game.rounds.count(), 0)

    def test_completed_game_accepts_no_new_players(self):
        self.add_players()
        self.game.start()
        self.game.complete()
        self.game.players.filter(color="blue").delete()

        with self.assertRaises(ValidationError):
            self.game.add_player(make_user("georgi"), "blue")

    def test_active_game_accepts_no_new_players(self):
        self.add_players()
        self.game.start()
        self.game.players.filter(color="blue").delete()

        with self.assertRaises(ValidationError):
            self.game.add_player(make_user("georgi"), "blue")

    def test_deleting_game_deletes_players_and_rounds(self):
        self.add_players()
        self.game.start()
        self.game.create_round(Round.TYPE_CITY_CAPTURE)

        self.game.delete()

        self.assertEqual(Player.objects.count(), 0)
        self.assertEqual(Round.objects.count(), 0)
