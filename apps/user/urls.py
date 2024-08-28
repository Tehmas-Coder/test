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
    path("verification", UserInvitaionLinkAPI.as_view({"get": "invitaion_link"})),
    path("resend-verification-link/", UserInvitaionLinkAPI.as_view({"post": "resend_verification_link"})),
    path("set-user-role/", UserViewSet.as_view({"post": "set_user_role"})),
    path("delete-role-with-permissions-from-sa-be/", RolePermissionViewSet.as_view({"delete": "delete_role_with_permissions"})),
    path("system-to-qb-login/", FromSaLoginToQBApiView.as_view()),
    path("update-role-permissions-from-sa-be/", RolePermissionViewSet.as_view({"put": "update_role_permissions_from_sa_be"})),
    path("system-user-create/", ForSytemUserAPI.as_view({"post": "system_user_create"})),
]

# ----------------------------------- USERS ---------------------------------- #
router.register(r"users", UserViewSet)

# ----------------------------- ROLE PERMISSIONS ----------------------------- #
router.register(r"roles", RoleViewSet)
router.register(r"permissions", PermissionViewSet)
router.register(r"role-permissions", RolePermissionViewSet)

urlpatterns += router.urls
