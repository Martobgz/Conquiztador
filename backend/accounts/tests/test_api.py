from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Profile

User = get_user_model()

CSRF_URL = "/api/auth/csrf/"
REGISTER_URL = "/api/auth/register/"
LOGIN_URL = "/api/auth/login/"
LOGOUT_URL = "/api/auth/logout/"
ME_URL = "/api/auth/me/"

PASSWORD = "example-password"


def make_user(username, email, nickname, password=PASSWORD):
    user = User.objects.create_user(username=username, email=email, password=password)
    Profile.objects.create(user=user, nickname=nickname)
    return user


class CsrfEndpointTests(TestCase):
    def test_csrf_endpoint_is_public_and_sets_the_cookie(self):
        response = self.client.get(CSRF_URL)

        self.assertEqual(response.status_code, 204)
        self.assertIn("csrftoken", response.cookies)


class RegistrationTests(TestCase):
    def test_successful_registration_creates_user_and_profile(self):
        payload = {
            "username": "player_one",
            "email": "player@example.com",
            "nickname": "MountainKnight",
            "password": PASSWORD,
            "password_confirm": PASSWORD,
        }

        response = self.client.post(
            REGISTER_URL, payload, content_type="application/json"
        )

        self.assertEqual(response.status_code, 201, response.content)
        user = User.objects.get(username="player_one")
        self.assertEqual(user.email, "player@example.com")
        self.assertEqual(user.profile.nickname, "MountainKnight")
        self.assertEqual(user.profile.avatar_key, "knight-1")
        # The stored password is a working hash, not the raw string.
        self.assertTrue(user.check_password(PASSWORD))

        body = response.json()
        self.assertEqual(
            body,
            {
                "id": user.id,
                "username": "player_one",
                "email": "player@example.com",
                "profile": {"nickname": "MountainKnight", "avatar_key": "knight-1"},
            },
        )
        self.assertNotIn("password", response.content.decode())

    def test_invalid_registration_is_rejected_with_the_offending_field(self):
        make_user("taken_user", "taken@example.com", "TakenNickname")
        base = {
            "username": "new_player",
            "email": "new@example.com",
            "nickname": "NewNickname",
            "password": PASSWORD,
            "password_confirm": PASSWORD,
        }
        cases = [
            ("username already taken", {"username": "taken_user"}, "username"),
            ("email already taken", {"email": "taken@example.com"}, "email"),
            ("nickname already taken", {"nickname": "TakenNickname"}, "nickname"),
            (
                "passwords do not match",
                {"password_confirm": "something-else"},
                "password_confirm",
            ),
        ]

        for label, override, expected_field in cases:
            with self.subTest(case=label):
                response = self.client.post(
                    REGISTER_URL, {**base, **override}, content_type="application/json"
                )

                self.assertEqual(response.status_code, 400, response.content)
                self.assertIn(expected_field, response.json()["errors"])
                # Only the pre-existing user survives a rejected registration.
                self.assertEqual(User.objects.count(), 1)


class LoginTests(TestCase):
    def setUp(self):
        self.user = make_user("player_one", "player@example.com", "MountainKnight")

    def test_successful_login_starts_a_session_usable_by_me(self):
        response = self.client.post(
            LOGIN_URL,
            {"username": "player_one", "password": PASSWORD},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["username"], "player_one")
        self.assertEqual(self.client.session["_auth_user_id"], str(self.user.id))

        me = self.client.get(ME_URL)
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["id"], self.user.id)

    def test_wrong_password_is_rejected_and_leaves_no_session(self):
        response = self.client.post(
            LOGIN_URL,
            {"username": "player_one", "password": "wrong-password"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("errors", response.json())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertIn(self.client.get(ME_URL).status_code, (401, 403))


class MePermissionTests(TestCase):
    def setUp(self):
        self.user = make_user("player_one", "player@example.com", "MountainKnight")
        self.other = make_user("player_two", "two@example.com", "ValleyKnight")

    def test_anonymous_access_is_denied(self):
        self.assertIn(self.client.get(ME_URL).status_code, (401, 403))

    def test_authenticated_user_only_ever_sees_their_own_data(self):
        self.client.force_login(self.user)

        body = self.client.get(ME_URL).json()

        self.assertEqual(body["id"], self.user.id)
        self.assertEqual(body["profile"]["nickname"], "MountainKnight")
        self.assertNotEqual(body["id"], self.other.id)


class ProfileUpdateTests(TestCase):
    def setUp(self):
        self.user = make_user("player_one", "player@example.com", "MountainKnight")
        self.client.force_login(self.user)

    def test_nickname_and_avatar_are_updated_and_persisted(self):
        response = self.client.patch(
            ME_URL,
            {"nickname": "NewKnight", "avatar_key": "knight-3"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json()["profile"],
            {"nickname": "NewKnight", "avatar_key": "knight-3"},
        )
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.nickname, "NewKnight")
        self.assertEqual(self.user.profile.avatar_key, "knight-3")

    def test_protected_fields_cannot_be_changed_through_me(self):
        response = self.client.patch(
            ME_URL,
            {
                "nickname": "NewKnight",
                "is_staff": True,
                "is_superuser": True,
                "username": "hacked",
                "email": "hacked@example.com",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.assertEqual(self.user.username, "player_one")
        self.assertEqual(self.user.email, "player@example.com")


class LogoutTests(TestCase):
    def test_logout_ends_the_session(self):
        make_user("player_one", "player@example.com", "MountainKnight")
        self.client.post(
            LOGIN_URL,
            {"username": "player_one", "password": PASSWORD},
            content_type="application/json",
        )
        self.assertEqual(self.client.get(ME_URL).status_code, 200)

        response = self.client.post(LOGOUT_URL)

        self.assertEqual(response.status_code, 204)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertIn(self.client.get(ME_URL).status_code, (401, 403))

    def test_anonymous_logout_is_denied(self):
        self.assertIn(self.client.post(LOGOUT_URL).status_code, (401, 403))


class CsrfEnforcementTests(TestCase):
    """The same unsafe request must fail without a CSRF token and pass with one."""

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.user = make_user("player_one", "player@example.com", "MountainKnight")
        self.client.force_login(self.user)

    def test_unsafe_request_without_csrf_token_is_forbidden(self):
        response = self.client.patch(ME_URL, {"nickname": "NoToken"}, format="json")

        self.assertEqual(response.status_code, 403, response.content)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.nickname, "MountainKnight")

    def test_same_request_succeeds_with_a_valid_csrf_token(self):
        self.client.get(CSRF_URL)
        token = self.client.cookies["csrftoken"].value

        response = self.client.patch(
            ME_URL,
            {"nickname": "WithToken"},
            format="json",
            headers={"x-csrftoken": token},
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.nickname, "WithToken")
