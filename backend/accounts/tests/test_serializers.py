from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import Profile
from accounts.serializers import RegisterSerializer

User = get_user_model()

VALID_PAYLOAD = {
    "username": "player_one",
    "email": "player@example.com",
    "nickname": "MountainKnight",
    "password": "example-password",
    "password_confirm": "example-password",
}


class RegisterSerializerTests(TestCase):
    def test_password_is_hashed_and_never_echoed_back(self):
        serializer = RegisterSerializer(data=VALID_PAYLOAD)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertNotEqual(user.password, "example-password")
        self.assertTrue(user.check_password("example-password"))
        # Both password fields are write_only, so they can never be rendered back.
        fields = RegisterSerializer().fields
        self.assertTrue(fields["password"].write_only)
        self.assertTrue(fields["password_confirm"].write_only)

    def test_weak_password_is_rejected_by_django_validators(self):
        serializer = RegisterSerializer(data={**VALID_PAYLOAD, "password": "123", "password_confirm": "123"})

        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_user_is_not_created_when_profile_creation_fails(self):
        serializer = RegisterSerializer(data=VALID_PAYLOAD)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        with patch.object(
            Profile.objects, "create", side_effect=RuntimeError("database is down")
        ):
            with self.assertRaises(RuntimeError):
                serializer.save()

        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Profile.objects.count(), 0)
