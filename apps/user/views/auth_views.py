from django.contrib.auth import login
from django.db import transaction
from rest_framework import status, views, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from apps.user.custom.auth_ninja import AuthNinja
from apps.user.custom.otp_ninja import OTPNinja
from apps.user.serializers.auth_serializers import LoginSerializer
from utils.rna_utils import color_print, make_error_response, make_success_response

from ..models.user_models import BaseUser


class RegisterApiView(views.APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        token = request.query_params.get("token")
        auth_ninja_instance = AuthNinja(token, request.data)
        response_data = auth_ninja_instance.register()
        return Response(response_data, status=201)


class LoginApiView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        request_data = request.data
        email: str = request_data.get("email")  # type: ignore
        exam_token = request.query_params.get("token")
        user = BaseUser.get_user_by_email(email)
        if not user:
            return make_error_response(message="User not found!")
        if exam_token:
            decrypted_data = AuthNinja.decrypt_exam_token(exam_token)
            AuthNinja.create_candidate_with_exam_token(user, decrypted_data)

        user_role_name = None
        if "is_system_user" in request_data:  # type: ignore
            user_role_name = user.roles.all().values().first()

        if user_role_name == None:
            if not user.is_verified:
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


class OTPViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def verify_otp(self, request, *args, **kwargs):
        email = request.data.get("email")
        otp = request.data.get("otp")
        if not otp:
            return Response({"error": "OTP is required"}, status=400)
        OTPNinja(email).verify_otp(otp)
        return make_success_response(message="User verified!")

    def resend_otp(self, request, *args, **kwargs):
        email = request.data.get("email")
        OTPNinja(email).resend_otp()
        return Response({"status": "sent", "message": "OTP sent!"})


class SaToQBLoginApiView(TokenObtainPairView):

    def post(self, request):
        if "is_system_user" not in request.data:
            return Response({"error": "Invalid request"}, status=status.HTTP_401_UNAUTHORIZED)
        email = request.data.get("email", None)
        if not email:
            return make_error_response(message="Email is required!")
        user = BaseUser.get_user_by_email(email)
        if not user:
            return make_error_response(message="User not found!")
        login(request, user)
        refresh = RefreshToken.for_user(user)
        auth_data = {"refresh": str(refresh), "access": str(refresh.access_token)}  # type: ignore
        return Response(auth_data, status=status.HTTP_200_OK)


class ExamTokenHandlerAPIView(views.APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        data = {}
        token = request.data.get("token")
        decrypted_data = AuthNinja.decrypt_exam_token(token)
        color_print(decrypted_data)
        user = BaseUser.objects.filter(email=decrypted_data["email"]).first()
        if not decrypted_data["is_public"]:
            if user:
                data["route"] = "login"
            else:
                data["route"] = "register"
        else:
            if not user:
                user = BaseUser.objects.create(email=decrypted_data["email"])
                user.set_password("12345678")
                user.save()
            AuthNinja.create_candidate_with_exam_token(user, decrypted_data)
            login(request, user)
            refresh = RefreshToken.for_user(user)
            data["refresh"] = str(refresh)
            data["access"] = str(refresh.access_token)  # type: ignore
            data["route"] = "exam"
        return Response(data, status=status.HTTP_200_OK)
