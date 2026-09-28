from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import Profile

User = get_user_model()


class UserModelTests(TestCase):
    def test_email_must_be_unique(self):
        User.objects.create_user(
            username="first", email="taken@example.com", password="example-password"
        )
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="second",
                email="taken@example.com",
                password="example-password",
            )


class ProfileModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="player_one",
            email="player@example.com",
            password="example-password",
        )

    def test_avatar_key_defaults_to_first_knight(self):
        profile = Profile.objects.create(user=self.user, nickname="MountainKnight")

        self.assertEqual(profile.avatar_key, "knight-1")
        self.assertEqual(self.user.profile, profile)

    def test_nickname_must_be_unique(self):
        Profile.objects.create(user=self.user, nickname="MountainKnight")
        other = User.objects.create_user(
            username="player_two", email="two@example.com", password="example-password"
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Profile.objects.create(user=other, nickname="MountainKnight")

    def test_profile_is_deleted_with_its_user(self):
        Profile.objects.create(user=self.user, nickname="MountainKnight")

        self.user.delete()

        self.assertEqual(Profile.objects.count(), 0)
