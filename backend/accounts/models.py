from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Project user. Email is unique so it can identify an account."""

    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username


class Profile(models.Model):
    """Game-facing data for a user: display name and chosen avatar."""

    AVATAR_KNIGHT_1 = "knight-1"
    AVATAR_KNIGHT_2 = "knight-2"
    AVATAR_KNIGHT_3 = "knight-3"
    AVATAR_KNIGHT_4 = "knight-4"

    AVATAR_CHOICES = [
        (AVATAR_KNIGHT_1, "Knight 1"),
        (AVATAR_KNIGHT_2, "Knight 2"),
        (AVATAR_KNIGHT_3, "Knight 3"),
        (AVATAR_KNIGHT_4, "Knight 4"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    nickname = models.CharField(max_length=30, unique=True)
    avatar_key = models.CharField(
        max_length=30,
        choices=AVATAR_CHOICES,
        default=AVATAR_KNIGHT_1,
    )

    def __str__(self):
        return self.nickname
