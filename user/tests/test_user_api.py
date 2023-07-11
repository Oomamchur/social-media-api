from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse, reverse_lazy
from rest_framework import status
from rest_framework.test import APIClient

from user.models import User
from user.serializers import UserListSerializer, UserDetailSerializer

USER_URL = reverse("user:user-list")
USER_UPDATE_URL = reverse("user:manage")


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


def detail_url(user_id: int):
    return reverse_lazy("user:user-detail", args=[user_id])


class UnauthenticatedUserApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self) -> None:
        response = self.client.get(USER_URL)

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

    def test_list_users(self) -> None:
        test_user()
        test_user(email="test2@test.com", username="spider")
        users = get_user_model().objects.all()
        serializer = UserListSerializer(users, many=True)

        response = self.client.get(USER_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_filter_by_username(self) -> None:
        user1 = test_user()
        user2 = test_user(email="test2@test.com", username="spider")
        serializer1 = UserListSerializer(user1)
        serializer2 = UserListSerializer(user2)

        response = self.client.get(USER_URL, {"username": "spider"})

        self.assertNotIn(serializer1.data, response.data["results"])
        self.assertIn(serializer2.data, response.data["results"])

    def test_filter_by_first_name(self) -> None:
        user1 = test_user()
        user2 = test_user(
            email="test2@test.com", username="spider", first_name="Bob"
        )
        serializer1 = UserListSerializer(user1)
        serializer2 = UserListSerializer(user2)

        response = self.client.get(USER_URL, {"first_name": "bob"})

        self.assertNotIn(serializer1.data, response.data["results"])
        self.assertIn(serializer2.data, response.data["results"])

    def test_filter_by_last_name(self) -> None:
        user1 = test_user()
        user2 = test_user(
            email="test2@test.com", username="spider", last_name="Brown"
        )
        serializer1 = UserListSerializer(user1)
        serializer2 = UserListSerializer(user2)

        response = self.client.get(USER_URL, {"last_name": "bro"})

        self.assertNotIn(serializer1.data, response.data["results"])
        self.assertIn(serializer2.data, response.data["results"])

    def test_retrieve_user(self) -> None:
        user = test_user()
        url = detail_url(user.id)
        serializer = UserDetailSerializer(user)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_user_forbidden(self) -> None:
        payload = {
            "email": "test1@test.com",
            "password": "test1234",
            "username": "test_username",
            "first_name": "test first_name",
            "last_name": "test last_name",
        }

        response = self.client.post(USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_user(self) -> None:
        payload = {"bio": "user_biography"}
        url = detail_url(self.user.id)

        response1 = self.client.patch(USER_UPDATE_URL, payload)
        response2 = self.client.get(url)

        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data["bio"], payload["bio"])

    def test_follow_user(self) -> None:
        user = test_user()
        url = detail_url(user.id)
        follow_url = url + "follow/"

        response1 = self.client.patch(follow_url)
        response2 = self.client.get(url)

        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertIn(self.user.__str__(), response2.data["user_followers"])


class AdminMovieSessionApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "admin1234", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_delete_user(self) -> None:
        user = test_user()
        url = detail_url(user.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
