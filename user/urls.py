from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from user.views import (
    CreateUserView,
    ManageUserView,
    LogoutView,
    PostViewSet,
    UserViewSet,
    LikeList,
)

router = routers.DefaultRouter()
router.register("posts", PostViewSet)
router.register("users", UserViewSet)

urlpatterns = [
    path("register/", CreateUserView.as_view(), name="create"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", ManageUserView.as_view(), name="manage"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("liked-posts/", LikeList.as_view(), name="liked-posts"),
    path("", include(router.urls)),
]

app_name = "user"
