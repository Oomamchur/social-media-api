from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse, reverse_lazy
from rest_framework import status
from rest_framework.test import APIClient

from user.models import User, Post, Comment, Like
from user.serializers import (
    PostListSerializer,
    PostDetailSerializer,
)

POST_URL = reverse("user:post-list")


def test_user(**params) -> User:
    defaults = {
        "email": "test@test.com",
        "password": "test1234",
        "username": "test_username",
        "first_name": "test_first_name",
        "last_name": "test_last_name",
    }
    defaults.update(**params)
    return get_user_model().objects.create_user(**defaults)


def test_post(**params) -> Post:
    defaults = {
        "text": "new_post",
    }
    defaults.update(**params)
    return Post.objects.create(**defaults)


def test_comment(**params) -> Post:
    defaults = {
        "text": "new_comment",
    }
    defaults.update(**params)
    return Comment.objects.create(**defaults)


def test_like(**params) -> Post:
    defaults = {
        "is_liked": "True",
    }
    defaults.update(**params)
    return Like.objects.create(**defaults)


def detail_url(post_id: int):
    return reverse_lazy("user:post-detail", args=[post_id])


class UnauthenticatedPostApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self) -> None:
        response = self.client.get(POST_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedUserApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="user1234",
            username="user_username",
            first_name="user_first_name",
            last_name="user_last_name",
        )
        self.client.force_authenticate(self.user)

    def test_list_posts(self) -> None:
        test_post(text="post", hashtag="post", user=self.user)
        test_post(text="new_post", hashtag="new", user=self.user)
        posts = Post.objects.all()
        serializer = PostListSerializer(posts, many=True)

        response = self.client.get(POST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_filter_by_hashtag(self) -> None:
        post1 = test_post(text="post", hashtag="post", user=self.user)
        post2 = test_post(text="new_post", hashtag="new", user=self.user)
        serializer1 = PostListSerializer(post1)
        serializer2 = PostListSerializer(post2)

        response = self.client.get(POST_URL, {"hashtag": "new"})

        self.assertNotIn(serializer1.data, response.data["results"])
        self.assertIn(serializer2.data, response.data["results"])

    def test_filter_by_username(self) -> None:
        new_user = test_user(username="spider")
        new_user.user_followers.add(self.user)
        post1 = test_post(text="post", hashtag="post", user=self.user)
        post2 = test_post(text="new_post", hashtag="new", user=new_user)
        serializer1 = PostListSerializer(post1)
        serializer2 = PostListSerializer(post2)

        response = self.client.get(POST_URL, {"username": "spider"})

        self.assertNotIn(serializer1.data, response.data["results"])
        self.assertIn(serializer2.data, response.data["results"])

    def test_retrieve_post(self) -> None:
        post = test_post(user=self.user)
        url = detail_url(post.id)
        serializer = PostDetailSerializer(post)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_update_my_post(self) -> None:
        post = test_post(user=self.user)
        url = detail_url(post.id)
        payload = {
            "text": "changed text",
        }

        response1 = self.client.patch(url, payload)
        response2 = self.client.get(url)

        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data["text"], payload["text"])

    def test_update_someone_post(self) -> None:
        new_user = test_user()
        new_user.user_followers.add(self.user)
        post = test_post(user=new_user)
        url = detail_url(post.id)
        payload = {"text": "changed text"}

        response = self.client.patch(url, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_comment_post(self) -> None:
        new_user = test_user()
        new_user.user_followers.add(self.user)
        post = test_post(user=new_user)
        test_comment(post=post, user=self.user)
        test_comment(text="another comment", post=post, user=self.user)
        url = detail_url(post.id)
        serializer = PostDetailSerializer(post)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["comments"], serializer.data["comments"]
        )

    def test_like_post(self) -> None:
        new_user = test_user()
        new_user.user_followers.add(self.user)
        post1 = test_post(user=new_user)
        post2 = test_post(user=self.user)
        test_like(post=post1, user=new_user)
        test_like(post=post1, user=self.user)
        test_like(post=post2, user=new_user)

        post1_likes = Like.objects.filter(post=post1).count()
        post2_likes = Like.objects.filter(post=post2).count()

        url1 = detail_url(post1.id)
        url2 = detail_url(post2.id)

        response1 = self.client.get(url1)
        response2 = self.client.get(url2)

        self.assertEqual(response1.data["likes_count"], post1_likes)
        self.assertEqual(response2.data["likes_count"], post2_likes)


class AdminMovieSessionApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "admin1234", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_delete_post(self) -> None:
        post = test_post(text="post", hashtag="post", user=self.user)
        url = detail_url(post.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
