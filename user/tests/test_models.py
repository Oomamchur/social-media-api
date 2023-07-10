from django.contrib.auth import get_user_model
from django.test import TestCase

from user.models import Post, Comment


class ModelsTests(TestCase):
    def test_user_str_with_bio(self) -> None:
        bio = "test biography"
        email = "test@test.com"
        password = "test1234"
        username = "username"
        first_name = "test first_name"
        last_name = "test last_name"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
            username=username,
            first_name=first_name,
            last_name=last_name,
            bio=bio,
        )

        self.assertEquals(user.bio, bio)
        self.assertTrue(user.check_password(password))
        self.assertEquals(str(user), f"{user.first_name} {user.last_name}")

    def test_comment_str(self) -> None:
        user = get_user_model().objects.create_user(
            email="test@test.com",
            password="test1234",
            username="username",
            first_name="test first_name",
            last_name="test last_name",
        )
        post = Post.objects.create(text="post text", user=user)
        comment = Comment.objects.create(
            user=user, post=post, text="comment text"
        )
        self.assertEquals(str(comment), comment.text)
