from django.urls import include, path
from rest_framework import routers

from apps.user.views.auth_views import *
from apps.user.views.role_views import *
from apps.user.views.user_views import *

router = routers.DefaultRouter()
# ----------------------------------- AUTH ----------------------------------- #
urlpatterns = [
    path("login/", LoginApiView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshApiView.as_view(), name="token_refresh"),
    path("logout/", LogoutApiView.as_view(), name="token_blacklist"),
    path("verify-otp/", OTPViewSet.as_view({"post": "verify_otp"}), name="verify_otp"),
    path("resend-otp/", OTPViewSet.as_view({"post": "resend_otp"}), name="resend_otp"),
]

# ----------------------------------- USERS ---------------------------------- #
router.register(r"users", UserViewSet)

# ----------------------------------- ROLES ---------------------------------- #
router.register(r"roles", RoleViewSet)
router.register(r"permissions", PermissionViewSet)

urlpatterns += router.urls
