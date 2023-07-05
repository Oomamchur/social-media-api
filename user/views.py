from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from user.models import Post
from user.pagination import UserPagination, PostPagination
from user.permissions import IsAdminOrIfAuthenticatedReadOnly
from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
    UserListSerializer,
    UserDetailSerializer,
    PostSerializer,
    PostDetailSerializer,
    PostListSerializer,
    UserFollowSerializer,
)


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    serializer_class = AuthTokenSerializer


class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request) -> Response:
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    pagination_class = UserPagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "list":
            return UserListSerializer
        if self.action == "retrieve":
            return UserDetailSerializer
        if self.action in ("follow", "unfollow"):
            return UserFollowSerializer

        return UserSerializer

    def get_queryset(self) -> queryset:
        queryset = super().get_queryset()

        username = self.request.query_params.get("username")
        if username:
            queryset = queryset.filter(username__icontains=username)

        first_name = self.request.query_params.get("first_name")
        if first_name:
            queryset = queryset.filter(first_name__icontains=first_name)

        last_name = self.request.query_params.get("last_name")
        if last_name:
            queryset = queryset.filter(last_name__icontains=last_name)

        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related("user_follow")

        return queryset.distinct()

    @action(
        methods=["PATCH"],
        detail=True,
        url_path="follow",
        permission_classes=(IsAuthenticated,),
    )
    def follow(self, request, pk=None):
        user = self.get_object()
        follower = self.request.user
        if user != follower and follower not in user.user_followers.all():
            user.user_followers.add(follower)
            user.save()

        return Response(status=status.HTTP_200_OK)

    @action(
        methods=["PATCH"],
        detail=True,
        url_path="unfollow",
        permission_classes=(IsAuthenticated,),
    )
    def unfollow(self, request, pk=None):
        user = self.get_object()
        follower = self.request.user
        if follower in user.user_followers.all():
            user.user_followers.remove(follower)
            user.save()

        return Response(status=status.HTTP_200_OK)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = PostPagination

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        if self.action == "retrieve":
            return PostDetailSerializer

        return PostListSerializer

    def get_permissions(self):
        if self.action == "retrieve":
            return [IsAdminOrIfAuthenticatedReadOnly]

        return super().get_permissions()

    def get_queryset(self):
        queryset = self.queryset

        hashtag = self.request.query_params.get("hashtag")
        if hashtag:
            queryset = queryset.filter(hashtag__icontains=hashtag)

        username = self.request.query_params.get("username")
        if username:
            queryset = queryset.filter(user__username__icontains=username)

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related("user")

        queryset = queryset.filter(
            Q(user=self.request.user) | Q(user__in=self.request.user.user_follow.all())
        )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
