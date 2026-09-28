from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Profile

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("nickname", "avatar_key")


class UserSerializer(serializers.ModelSerializer):
    """Read-only representation returned by every auth endpoint."""

    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "profile")
        read_only_fields = fields

    def get_profile(self, user):
        # Reverse one-to-one raises an AttributeError subclass when absent.
        profile = getattr(user, "profile", None)
        return ProfileSerializer(profile).data if profile is not None else None


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="User with this username already exists.",
            )
        ],
    )
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="User with this email already exists.",
            )
        ],
    )
    nickname = serializers.CharField(
        max_length=30,
        validators=[
            UniqueValidator(
                queryset=Profile.objects.all(),
                message="Profile with this nickname already exists.",
            )
        ],
    )
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": ["Passwords do not match."]}
            )
        try:
            validate_password(attrs["password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """Create the user and its profile together, or neither."""
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        Profile.objects.create(user=user, nickname=validated_data["nickname"])
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["username"],
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError(
                {"detail": ["Invalid username or password."]}
            )
        attrs["user"] = user
        return attrs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """The only fields a user may change on their own profile."""

    class Meta:
        model = Profile
        fields = ("nickname", "avatar_key")
