from django.urls import include, path
from rest_framework import routers

from apps.user.views.auth_views import *
from apps.user.views.role_permission_views import *
from apps.user.views.user_views import *

router = routers.DefaultRouter()
# ----------------------------------- AUTH ----------------------------------- #
urlpatterns = [
    path("register/", RegisterApiView.as_view(), name="register"),
    path("login/", LoginApiView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshApiView.as_view(), name="token_refresh"),
    path("logout/", LogoutApiView.as_view(), name="token_blacklist"),
    path("verify-otp/", OTPViewSet.as_view({"post": "verify_otp"}), name="verify_otp"),
    path("resend-otp/", OTPViewSet.as_view({"post": "resend_otp"}), name="resend_otp"),
    path("verification", InvitaionLinkAPI.as_view(), name="invitation_link"),
    path("resend-verification-link/", ResendVerificationLinkAPI.as_view(), name="resend_verification_link"),
    path("set-user-role/", SetUserRoleAPI.as_view(), name="set_user_role"),
    path("update-role-permissions-from-sa-be/", RolePermissionViewSet.as_view({"put": "update_role_permissions_from_sa_be"})),
]

# ----------------------------------- USERS ---------------------------------- #
router.register(r"users", UserViewSet)

# ----------------------------- ROLE PERMISSIONS ----------------------------- #
router.register(r"roles", RoleViewSet)
router.register(r"permissions", PermissionViewSet)
router.register(r"role-permissions", RolePermissionViewSet)

urlpatterns += router.urls
