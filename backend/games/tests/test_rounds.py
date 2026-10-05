from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from games.models import Game, Round

User = get_user_model()


def make_active_game(prefix):
    game = Game.objects.create()
    for color in ("red", "green", "blue"):
        user = User.objects.create_user(
            username=f"{prefix}_{color}", email=f"{prefix}_{color}@example.com"
        )
        game.add_player(user, color)
    game.start()
    return game


class RoundCreationTests(TestCase):
    def setUp(self):
        self.game = make_active_game("first")

    def test_create_round(self):
        new_round = self.game.create_round(Round.TYPE_CITY_CAPTURE)

        self.assertEqual(new_round.game, self.game)
        self.assertEqual(new_round.number, 1)
        self.assertEqual(new_round.type, "city_capture")
        self.assertEqual(new_round.status, "pending")
        self.assertIsNone(new_round.winner)
        self.assertIsNone(new_round.completed_at)
        self.assertIsNotNone(new_round.created_at)
        self.assertIn(new_round, self.game.rounds.all())

    def test_type_must_be_a_known_choice(self):
        with self.assertRaises(ValidationError):
            self.game.create_round("duel")

    def test_round_numbers_follow_each_other(self):
        first = self.game.create_round(Round.TYPE_CITY_CAPTURE)
        first.start()
        first.complete(self.game.players.first())

        second = self.game.create_round(Round.TYPE_BATTLE)

        self.assertEqual(second.number, 2)

    def test_next_round_waits_for_current_round(self):
        self.game.create_round(Round.TYPE_CITY_CAPTURE)

        with self.assertRaises(ValidationError):
            self.game.create_round(Round.TYPE_BATTLE)
        self.assertEqual(self.game.rounds.count(), 1)

    def test_waiting_game_accepts_no_rounds(self):
        waiting_game = Game.objects.create()

        with self.assertRaises(ValidationError):
            waiting_game.create_round(Round.TYPE_BONUS)

    def test_round_number_is_unique_per_game(self):
        Round.objects.create(game=self.game, number=1, type=Round.TYPE_BATTLE)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Round.objects.create(game=self.game, number=1, type=Round.TYPE_BONUS)

    def test_duplicate_round_number_fails_validation(self):
        Round.objects.create(
            game=self.game,
            number=1,
            type=Round.TYPE_BATTLE,
            status=Round.STATUS_COMPLETED,
            winner=self.game.players.first(),
            completed_at=timezone.now(),
        )

        with self.assertRaises(ValidationError):
            Round(game=self.game, number=1, type=Round.TYPE_BONUS).full_clean()

    def test_same_round_number_allowed_in_different_games(self):
        other_game = make_active_game("second")

        self.game.create_round(Round.TYPE_BATTLE)
        other_game.create_round(Round.TYPE_BATTLE)

        self.assertEqual(Round.objects.filter(number=1).count(), 2)


class RoundLifecycleTests(TestCase):
    def setUp(self):
        self.game = make_active_game("first")
        self.round = self.game.create_round(Round.TYPE_BATTLE)
        self.player = self.game.players.get(color="red")

    def test_start_round(self):
        self.round.start()

        self.round.refresh_from_db()
        self.assertEqual(self.round.status, "active")

    def test_complete_round_with_winner_from_same_game(self):
        self.round.start()

        self.round.complete(self.player)

        self.round.refresh_from_db()
        self.assertEqual(self.round.status, "completed")
        self.assertEqual(self.round.winner, self.player)
        self.assertIsNotNone(self.round.completed_at)

    def test_winner_from_another_game_is_rejected(self):
        other_player = make_active_game("second").players.get(color="red")
        self.round.start()

        with self.assertRaises(ValidationError):
            self.round.complete(other_player)

        self.assertEqual(self.round.status, "active")
        self.assertIsNone(self.round.winner)
        self.round.refresh_from_db()
        self.assertEqual(self.round.status, "active")
        self.assertIsNone(self.round.winner)

    def test_pending_round_cannot_be_completed(self):
        with self.assertRaises(ValidationError):
            self.round.complete(self.player)
        self.assertEqual(self.round.status, "pending")

    def test_completed_round_needs_a_winner(self):
        self.round.start()

        with self.assertRaises(ValidationError):
            self.round.complete(None)

    def test_completed_round_needs_completed_at(self):
        self.round.start()
        self.round.status = Round.STATUS_COMPLETED
        self.round.winner = self.player

        with self.assertRaises(ValidationError):
            self.round.full_clean()

    def test_unfinished_round_has_no_winner(self):
        self.round.winner = self.player

        with self.assertRaises(ValidationError):
            self.round.full_clean()

    def test_active_round_cannot_be_started_again(self):
        self.round.start()

        with self.assertRaises(ValidationError):
            self.round.start()

    def test_completed_round_cannot_be_completed_again(self):
        other_player = self.game.players.get(color="blue")
        self.round.start()
        self.round.complete(self.player)

        with self.assertRaises(ValidationError):
            self.round.complete(other_player)

        self.round.refresh_from_db()
        self.assertEqual(self.round.winner, self.player)

    def test_completed_round_cannot_be_reopened(self):
        self.round.start()
        self.round.complete(self.player)
        self.round.status = Round.STATUS_ACTIVE
        self.round.winner = None
        self.round.completed_at = None

        with self.assertRaises(ValidationError):
            self.round.full_clean()

    def test_only_one_active_round_per_game(self):
        self.round.start()

        with self.assertRaises(IntegrityError), transaction.atomic():
            Round.objects.create(
                game=self.game, number=2, type=Round.TYPE_BONUS, status="active"
            )

    def test_winner_is_cleared_when_player_is_deleted(self):
        self.round.start()
        self.round.complete(self.player)

        self.player.user.delete()

        self.round.refresh_from_db()
        self.assertIsNone(self.round.winner)


class CurrentRoundTests(TestCase):
    def setUp(self):
        self.game = make_active_game("first")

    def test_no_rounds_means_no_current_round(self):
        self.assertIsNone(self.game.get_current_round())

    def test_current_round_has_the_highest_number(self):
        for number in (1, 3, 2):
            Round.objects.create(game=self.game, number=number, type=Round.TYPE_BATTLE)

        self.assertEqual(self.game.get_current_round().number, 3)

    def test_current_round_moves_forward(self):
        first = self.game.create_round(Round.TYPE_CITY_CAPTURE)
        self.assertEqual(self.game.get_current_round(), first)

        first.start()
        first.complete(self.game.players.first())
        second = self.game.create_round(Round.TYPE_CAPITAL_ATTACK)

        self.assertEqual(self.game.get_current_round(), second)
