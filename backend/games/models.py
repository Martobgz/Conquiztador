from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class StatusLifecycle:
    """
    A status that only moves forward along STATUS_TRANSITIONS.

    Subclasses define STATUS_TRANSITIONS and INITIAL_STATUS.
    """

    def status_transition_error(self):
        """Why the unsaved status change is not allowed, or None if it is."""
        previous = self.INITIAL_STATUS
        if self.pk is not None:
            previous = (
                type(self)
                .objects.filter(pk=self.pk)
                .values_list("status", flat=True)
                .first()
            ) or previous
        if self.status == previous or self.status in self.STATUS_TRANSITIONS[previous]:
            return None
        return f"A {self._meta.verbose_name} cannot go from {previous} to {self.status}."

    def move_to(self, status, **fields):
        """Move to the next status, validate, and save. Nothing changes on error."""
        if status not in self.STATUS_TRANSITIONS.get(self.status, ()):
            raise ValidationError(
                {
                    "status": f"A {self._meta.verbose_name} cannot go from "
                    f"{self.status} to {status}."
                }
            )
        changes = {"status": status, **fields}
        previous = {name: getattr(self, name) for name in changes}
        for name, value in changes.items():
            setattr(self, name, value)
        try:
            self.full_clean()
        except ValidationError:
            for name, value in previous.items():
                setattr(self, name, value)
            raise
        self.save(update_fields=list(changes))


class Game(StatusLifecycle, models.Model):
    """One match between three players, played as a series of rounds."""

    PLAYERS_PER_GAME = 3

    STATUS_WAITING = "waiting"
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"

    STATUS_CHOICES = [
        (STATUS_WAITING, "Waiting"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_COMPLETED, "Completed"),
    ]

    # The only moves a game's status can make: waiting -> active -> completed.
    INITIAL_STATUS = STATUS_WAITING
    STATUS_TRANSITIONS = {
        STATUS_WAITING: {STATUS_ACTIVE},
        STATUS_ACTIVE: {STATUS_COMPLETED},
        STATUS_COMPLETED: set(),
    }

    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_WAITING,
    )

    def __str__(self):
        return f"Game #{self.pk}"

    def get_current_round(self):
        return self.rounds.order_by("-number").first()

    def is_active(self):
        return self.status == "active"

    def is_completed(self):
        return self.status == "completed"

    def clean(self):
        super().clean()
        transition_error = self.status_transition_error()
        if transition_error:
            raise ValidationError({"status": transition_error})
        if self.status == self.STATUS_WAITING:
            return

        player_count = self.players.count() if self.pk else 0
        if player_count != self.PLAYERS_PER_GAME:
            raise ValidationError(
                {
                    "status": f"A game needs exactly {self.PLAYERS_PER_GAME} "
                    f"players to be {self.status}, not {player_count}."
                }
            )
        if (
            self.status == self.STATUS_COMPLETED
            and self.rounds.exclude(status=Round.STATUS_COMPLETED).exists()
        ):
            raise ValidationError(
                {"status": "Finish the current round before completing the game."}
            )

    def add_player(self, user, color):
        player = Player(game=self, user=user, color=color)
        player.full_clean()
        player.save()
        return player

    def start(self):
        self.move_to(self.STATUS_ACTIVE)

    def complete(self):
        self.move_to(self.STATUS_COMPLETED)

    def create_round(self, round_type):
        current = self.get_current_round()
        new_round = Round(
            game=self,
            number=current.number + 1 if current else 1,
            type=round_type,
        )
        new_round.full_clean()
        new_round.save()
        return new_round


class Player(models.Model):
    """A user's seat in one game: their color and score in that game."""

    COLOR_RED = "red"
    COLOR_GREEN = "green"
    COLOR_BLUE = "blue"

    COLOR_CHOICES = [
        (COLOR_RED, "Red"),
        (COLOR_GREEN, "Green"),
        (COLOR_BLUE, "Blue"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="players",
    )
    score = models.IntegerField(default=0)
    color = models.CharField(max_length=10, choices=COLOR_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "game"],
                name="unique_user_per_game",
            ),
            models.UniqueConstraint(
                fields=["game", "color"],
                name="unique_color_per_game",
            ),
            models.CheckConstraint(
                condition=models.Q(score__gte=0),
                name="player_score_gte_0",
            ),
        ]

    def __str__(self):
        return f"{self.user} ({self.color})"

    def clean(self):
        super().clean()
        # Only joining is restricted; existing players keep updating their score.
        if self.pk is not None or self.game_id is None:
            return
        if self.game.status != Game.STATUS_WAITING:
            raise ValidationError(
                {"game": "Players can only join a game that is waiting to start."}
            )
        if self.game.players.count() >= Game.PLAYERS_PER_GAME:
            raise ValidationError(
                {"game": f"A game cannot have more than {Game.PLAYERS_PER_GAME} players."}
            )


class Round(StatusLifecycle, models.Model):
    """One numbered round of a game, won by one of that game's players."""

    TYPE_CITY_CAPTURE = "city_capture"
    TYPE_BATTLE = "battle"
    TYPE_CAPITAL_ATTACK = "capital_attack"
    TYPE_BONUS = "bonus"

    TYPE_CHOICES = [
        (TYPE_CITY_CAPTURE, "City capture"),
        (TYPE_BATTLE, "Battle"),
        (TYPE_CAPITAL_ATTACK, "Capital attack"),
        (TYPE_BONUS, "Bonus"),
    ]

    STATUS_PENDING = "pending"
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_COMPLETED, "Completed"),
    ]

    # The only moves a round's status can make: pending -> active -> completed.
    INITIAL_STATUS = STATUS_PENDING
    STATUS_TRANSITIONS = {
        STATUS_PENDING: {STATUS_ACTIVE},
        STATUS_ACTIVE: {STATUS_COMPLETED},
        STATUS_COMPLETED: set(),
    }

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="rounds",
    )
    number = models.PositiveIntegerField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    winner = models.ForeignKey(
        Player,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["game", "number"],
                name="unique_round_number_per_game",
            ),
            models.UniqueConstraint(
                fields=["game"],
                condition=models.Q(status="active"),
                name="one_active_round_per_game",
                violation_error_message="A game can have only one active round.",
            ),
        ]

    def __str__(self):
        return f"{self.game} round {self.number}"

    def clean(self):
        super().clean()
        errors = {}

        transition_error = self.status_transition_error()
        if transition_error:
            errors["status"] = transition_error

        if self.game_id is not None:
            if self.pk is None and self.game.status != Game.STATUS_ACTIVE:
                errors["game"] = "Rounds can only be created in an active game."
            elif (
                self.pk is None
                and self.game.rounds.exclude(status=self.STATUS_COMPLETED).exists()
            ):
                errors["game"] = "Finish the current round before creating the next one."
            elif (
                self.status == self.STATUS_ACTIVE
                and self.game.status != Game.STATUS_ACTIVE
            ):
                errors["status"] = "A round can only be active in an active game."

        if self.status == self.STATUS_COMPLETED:
            if self.winner_id is None:
                errors["winner"] = "A completed round needs a winner."
            if self.completed_at is None:
                errors["completed_at"] = "A completed round needs a completion time."
        else:
            if self.winner_id is not None:
                errors["winner"] = "Only a completed round can have a winner."
            if self.completed_at is not None:
                errors["completed_at"] = "Only a completed round can have a completion time."

        if (
            self.winner_id is not None
            and self.game_id is not None
            and self.winner.game_id != self.game_id
        ):
            errors["winner"] = "The winner must be a player in this game."

        if errors:
            raise ValidationError(errors)

    def start(self):
        self.move_to(self.STATUS_ACTIVE)

    def complete(self, winner):
        self.move_to(self.STATUS_COMPLETED, winner=winner, completed_at=timezone.now())
