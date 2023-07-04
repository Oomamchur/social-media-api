from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from user.models import Post


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "email",
            "password",
            "username",
            "first_name",
            "last_name",
            "bio",
            "other_details",
            "image",
            "is_staff",
        )
        read_only_fields = (
            "id",
            "is_staff",
        )
        extra_kwargs = {"password": {"write_only": True, "min_length": 8}}

    def create(self, validated_data):
        """Create a new user with encrypted password and return it"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update a user, set the password correctly and return it"""
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()

        return user


class UserListSerializer(UserSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "image",
            "followers_count",
            "following_count",
        )


class UserDetailSerializer(UserSerializer):
    user_follow = serializers.StringRelatedField(many=True)
    user_followers = serializers.StringRelatedField(many=True)

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "username",
            "image",
            "first_name",
            "last_name",
            "bio",
            "other_details",
            "user_follow",
            "user_followers",
        )


class UserFollowSerializer(UserSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "user_followers",
        )


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(email=email, password=password)

            if not user:
                raise ValidationError("Unable to log in with provided credentials.")
        else:
            raise ValidationError("Must include 'email' and 'password'.")

        attrs["user"] = user
        return attrs


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("id", "hashtag", "text", "user", "media_image")


class PostListSerializer(PostSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Post
        fields = ("id", "hashtag", "text", "user_username", "media_image")


class PostDetailSerializer(PostSerializer):
    user = UserListSerializer(many=False, read_only=True)
