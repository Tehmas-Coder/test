from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from apps.user.serializers.user_serializers import LoginSerializer
from utils.rna_utils import make_error_response, make_success_response

from ..models import BaseUser


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


class OTPViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def verify_otp(self, request, *args, **kwargs):
        user = get_object_or_404(BaseUser, email=request.data.get("email", None))
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

    def resend_otp(self, request, *args, **kwargs):
        user = get_object_or_404(BaseUser, email=request.data.get("email", None))
        if not user:
            return Response(self.USER_NOT_FOUND, status=404)
        if user.is_verified:
            return make_error_response(message="User is already verified!")
        otp_sent = user.send_otp()
        if not otp_sent:
            return make_error_response(message="Failed to send OTP, please try again")
        return Response({"status": "sent", "message": "OTP sent!"})
