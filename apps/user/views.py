from rest_framework import viewsets
from rest_framework.request import Request
from apps.user.serializers.user_serializers import (
    LoginSerializer,
    UserDetailSerializer,
    UserEditSerializer,
)
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenBlacklistView,
    TokenRefreshView,
)
from custom.permissions.permissions import IsSuperAdmin
from apps.user.serializers.role_serializers import RoleSerializer
from apps.user.models import Permission, Resource, Role
from apps.user.serializers.permission_serializers import PermissionSerializer
from utils.rna_utils import (
    make_error_response,
    make_success_response,
)
from apps.user.filters.user_filter import UserFilter
from apps.user.serializers.resource_serializers import ResourceSerializer
from .models import BaseUser
from utils.rna_utils import debug_print


# ---------------------------------------------------------------------------- #
#                                     AUTH                                     #
# ---------------------------------------------------------------------------- #
class LoginApiView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get("email", None)  # type: ignore
        if not email:
            return make_error_response(message="Email is required!")
        user = BaseUser.get_user_by_email(email)
        if not user:
            return make_error_response(message="User not found!")
        if not user.is_verified:  # type: ignore
            return make_error_response(message="User is not verified!")
        return super().post(request, *args, **kwargs)


class LogoutApiView(TokenBlacklistView):
    permission_classes = [AllowAny]

    def post(self, request: Request, *args, **kwargs) -> Response:
        return super().post(request, *args, **kwargs)


class TokenRefreshApiView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs) -> Response:
        return super().post(request, *args, **kwargs)


# ---------------------------------------------------------------------------- #
#                                     USER                                     #
# ---------------------------------------------------------------------------- #


class UserViewSet(viewsets.ModelViewSet):
    queryset = BaseUser.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_class = UserFilter
    USER_NOT_FOUND = {"error": "User not found"}
    USER_STATUSES = ["active", "inactive", "deleted"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return UserEditSerializer

        return super().get_serializer_class()

    def get_permissions(self):
        if self.action in ["create", "verify_otp", "resend_otp"]:
            return (AllowAny(),)
        elif self.action in [
            "restore",
            "destroy",
        ]:
            return (IsSuperAdmin(),)
        return super().get_permissions()

    def get_object(self, id: int | None = None):
        try:
            return BaseUser.objects.get(pk=id or self.kwargs.get("pk"))
        except BaseUser.DoesNotExist:
            return None

    # ------------------------------------ API ----------------------------------- #

    def list(self, request, *args, **kwargs):
        self.queryset = self.queryset.filter(meta_status="active")
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        request.data["is_staff"] = True
        request.data["is_superuser"] = False
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        if "email" in serializer.errors:
            return Response(
                {"error": "User with this email already exists"}, status=400
            )
        return Response(serializer.errors, status=400)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object(id=kwargs.get("pk"))
        if not instance:
            return Response(self.USER_NOT_FOUND, status=404)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object(id=kwargs.get("pk"))
        if not instance:
            return Response({"error": "User not found"}, status=404)
        instance.deactivate()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def restore(self, request, *args, **kwargs):
        instance = self.get_object(id=kwargs.get("pk"))
        if not instance:
            return Response(self.USER_NOT_FOUND, status=404)
        instance.activate()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="bulk-delete")
    def bulk_delete(self, request):
        user_ids = request.data.get("users", [])
        users = BaseUser.objects.filter(id__in=user_ids)
        for user in users:
            user.delete()
        return Response({"status": "deleted", "message": "Users deleted!"})

    @action(detail=True, methods=["post"], url_path="verify-otp")
    def verify_otp(self, request, *args, **kwargs):
        user = self.get_object(id=kwargs.get("pk"))
        if not user:
            return Response(self.USER_NOT_FOUND, status=404)
        if user.is_verified:
            return make_error_response(message="User is already verified!")
        otp = request.data.get("otp")
        if not otp:
            return Response({"error": "OTP is required"}, status=400)
        if not user.verify_otp(otp):
            return make_error_response(message="Invalid OTP")
        return make_success_response(message="User verified!")

    @action(detail=True, methods=["post"], url_path="resend-otp")
    def resend_otp(self, request, *args, **kwargs):
        user = self.get_object(id=kwargs.get("pk"))
        if not user:
            return Response(self.USER_NOT_FOUND, status=404)
        if user.is_verified:
            return make_error_response(message="User is already verified!")
        otp_sent = user.send_otp()
        if not otp_sent:
            return make_error_response(message="Failed to send OTP, please try again")
        return Response({"status": "sent", "message": "OTP sent!"})


# ---------------------------------------------------------------------------- #
#                                     ROLES                                    #
# ---------------------------------------------------------------------------- #


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = (permissions.IsAuthenticated,)


# ---------------------------------------------------------------------------- #
#                                  PERMISSIONS                                 #
# ---------------------------------------------------------------------------- #


class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = (permissions.IsAuthenticated,)


# ---------------------------------------------------------------------------- #
#                                   RESOURCES                                  #
# ---------------------------------------------------------------------------- #


class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = (permissions.IsAuthenticated,)
