from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from games.models import Game, Player

User = get_user_model()


def make_user(username):
    return User.objects.create_user(username=username, email=f"{username}@example.com")


class PlayerTests(TestCase):
    def setUp(self):
        self.game = Game.objects.create()
        self.ana = make_user("ana")
        self.boris = make_user("boris")

    def test_player_joins_with_zero_score(self):
        player = self.game.add_player(self.ana, "red")

        self.assertEqual(player.score, 0)
        self.assertEqual(player.game, self.game)
        self.assertEqual(player.user, self.ana)
        self.assertIn(player, self.game.players.all())

    def test_three_different_users_and_colors(self):
        vera = make_user("vera")

        self.game.add_player(self.ana, "red")
        self.game.add_player(self.boris, "green")
        self.game.add_player(vera, "blue")

        self.assertEqual(self.game.players.count(), 3)

    def test_color_must_be_red_green_or_blue(self):
        with self.assertRaises(ValidationError):
            self.game.add_player(self.ana, "yellow")

    def test_score_can_be_updated(self):
        player = self.game.add_player(self.ana, "red")

        player.score = 300
        player.full_clean()
        player.save()

        player.refresh_from_db()
        self.assertEqual(player.score, 300)


class PlayerConstraintTests(TestCase):
    def setUp(self):
        self.game = Game.objects.create()
        self.ana = make_user("ana")
        self.boris = make_user("boris")

    def test_same_user_twice_in_a_game_fails_validation(self):
        self.game.add_player(self.ana, "red")

        with self.assertRaises(ValidationError):
            self.game.add_player(self.ana, "green")
        self.assertEqual(self.game.players.count(), 1)

    def test_same_user_twice_in_a_game_is_rejected_by_database(self):
        Player.objects.create(game=self.game, user=self.ana, color="red")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Player.objects.create(game=self.game, user=self.ana, color="green")

    def test_same_color_twice_in_a_game_fails_validation(self):
        self.game.add_player(self.ana, "red")

        with self.assertRaises(ValidationError):
            self.game.add_player(self.boris, "red")
        self.assertEqual(self.game.players.count(), 1)

    def test_same_color_twice_in_a_game_is_rejected_by_database(self):
        Player.objects.create(game=self.game, user=self.ana, color="red")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Player.objects.create(game=self.game, user=self.boris, color="red")

    def test_negative_score_fails_validation(self):
        player = self.game.add_player(self.ana, "red")
        player.score = -1

        with self.assertRaises(ValidationError):
            player.full_clean()

    def test_negative_score_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Player.objects.create(game=self.game, user=self.ana, color="red", score=-1)

    def test_same_user_and_color_allowed_in_different_games(self):
        other_game = Game.objects.create()

        self.game.add_player(self.ana, "red")
        other_game.add_player(self.ana, "red")

        self.assertEqual(Player.objects.filter(user=self.ana).count(), 2)

    def test_player_is_deleted_with_its_user(self):
        self.game.add_player(self.ana, "red")

        self.ana.delete()

        self.assertEqual(self.game.players.count(), 0)
