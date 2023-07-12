import os
import uuid

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext as _


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


def user_image_file_path(instance, filename) -> str:
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.last_name)}-{uuid.uuid4()}{extension}"

    return os.path.join("media/uploads/users/", filename)


class User(AbstractUser):
    email = models.EmailField(_("email"), unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    username = models.CharField(max_length=60, unique=True)
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    bio = models.TextField(blank=True)
    other_details = models.TextField(blank=True)
    image = models.ImageField(null=True, blank=True, upload_to=user_image_file_path)
    user_follow = models.ManyToManyField(
        "User", blank=True, related_name="user_followers", symmetrical=False
    )

    @property
    def followers_count(self):
        return self.user_followers.count()

    @property
    def following_count(self):
        return self.user_follow.count()

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


def post_image_file_path(instance, filename) -> str:
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.hashtag)}-{uuid.uuid4()}{extension}"

    return os.path.join("media/uploads/users/posts", filename)


class Post(models.Model):
    hashtag = models.CharField(max_length=60, blank=True)
    text = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="posts",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    media_image = models.ImageField(null=True, upload_to=post_image_file_path)

    @property
    def comments_count(self):
        return self.comments.count()

    @property
    def likes_count(self):
        return self.likes.filter(is_liked=True).count()

    class Meta:
        ordering = ["-created_at"]


class Comment(models.Model):
    post = models.ForeignKey(
        Post, related_name="comments", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="comments",
        on_delete=models.CASCADE
    )
    text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.text


class Like(models.Model):
    post = models.ForeignKey(
        Post, related_name="likes", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="likes",
        on_delete=models.CASCADE,
    )
    is_liked = models.BooleanField()

    class Meta:
        unique_together = ("post", "user")
