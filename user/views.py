from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from user.models import Post, Comment, Like
from user.pagination import UserPagination, PostPagination
from user.permissions import (
    IsAdminOrIfAuthenticatedReadOnly,
    IsCreatorOrReadOnly,
)
from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
    UserListSerializer,
    UserDetailSerializer,
    UserFollowSerializer,
    PostSerializer,
    PostDetailSerializer,
    PostListSerializer,
    CommentSerializer,
    LikeSerializer,
    LikeListSerializer,
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

        queryset = queryset.prefetch_related("user_follow")

        return queryset.distinct()

    @action(
        methods=["PATCH"],
        detail=True,
        url_path="follow",
        permission_classes=(IsAuthenticated,),
    )
    def follow(self, request, pk=None):
        """Endpoint for following specific user"""
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
        """Endpoint for unfollowing specific user"""
        user = self.get_object()
        follower = self.request.user
        if follower in user.user_followers.all():
            user.user_followers.remove(follower)
            user.save()

        return Response(status=status.HTTP_200_OK)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    pagination_class = PostPagination

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        if self.action == "retrieve":
            return PostDetailSerializer
        if self.action == "add_comment":
            return CommentSerializer
        if self.action == "like":
            return LikeSerializer

        return PostListSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsCreatorOrReadOnly()]

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
            queryset = queryset.prefetch_related("user")

        queryset = queryset.filter(
            Q(user=self.request.user)
            | Q(user__in=self.request.user.user_follow.all())
        )

        return queryset

    @action(
        methods=["POST"],
        detail=True,
        url_path="add_comment",
        permission_classes=(IsAuthenticated,),
    )
    def add_comment(self, request, pk=None):
        """Endpoint for adding comment to specific post"""
        post = self.get_object()
        user = self.request.user
        Comment.objects.create(post=post, user=user, text=request.data["text"])

        return Response(status=status.HTTP_200_OK)

    @action(
        methods=["POST"],
        detail=True,
        url_path="like",
        permission_classes=(IsAuthenticated,),
    )
    def like(self, request, pk=None):
        """Endpoint for liking specific post"""
        post = self.get_object()
        user = self.request.user
        try:
            like = Like.objects.get(post=post, user=user)
            if like.is_liked:
                like.is_liked = False
            else:
                like.is_liked = True
            like.save()
        except Like.DoesNotExist:
            Like.objects.create(post=post, user=user, is_liked=True)

        return Response(status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class LikeList(generics.ListAPIView):
    queryset = Like.objects.all()
    serializer_class = LikeListSerializer

    def get_queryset(self):
        queryset = self.queryset.select_related("post")
        user = self.request.user

        queryset = queryset.filter(user=user, is_liked=True)

        return queryset
