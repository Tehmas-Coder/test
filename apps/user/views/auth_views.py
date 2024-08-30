from django.contrib.auth import login
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status, views, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from apps.exam_public.models.exam_public_models import Candidate
from apps.user.serializers.user_serializers import LoginSerializer, UserEditSerializer
from utils.rna_utils import make_error_response, make_success_response

from ..models import BaseUser, Role


class RegisterApiView(views.APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if "is_superuser" in request.data:
            try:
                request.data["is_verified"] = True
                super_user_instance = BaseUser.objects.create_superuser(
                    email=request.data.pop("email"),
                    password=request.data.pop("password"),
                    **request.data,
                )
                serializer = UserEditSerializer(super_user_instance)
                return Response(serializer.data, status=201)
            except Exception as e:
                return make_error_response(message=f"{str(e)}")

        else:
            serializer = UserEditSerializer(data=request.data)
            if serializer.is_valid():
                candidate_instance = serializer.save()
                role_id = Role.objects.filter(name__icontains="Candidate").values("id").first()
                candidate_instance.roles.add(role_id["id"])
                if not candidate_instance.send_otp():
                    transaction.set_rollback(True)
                    raise serializers.ValidationError({"error": "Failed to send email, please try again"})

                Candidate.objects.create(user_id=serializer.data["id"])
                return Response(serializer.data, status=201)
            if "email" in serializer.errors:
                return Response({"error": "User with this email already exists"}, status=400)
            return Response(serializer.errors, status=400)


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

        user_role_name = None
        if "is_system_user" in request.data:
            user_role_name = user.roles.all().values().first()

        if user_role_name == None:
            if not user.is_verified:  # type: ignore
                return make_error_response(message="User is not verified!")
        else:
            pass

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


class FromSaLoginToQBApiView(TokenObtainPairView):

    def post(self, request):

        if "is_system_user" in request.data:
            email = request.data.get("email", None)
            # email = "john.doe@example.com"

            if not email:
                return make_error_response(message="Email is required!")
            user = BaseUser.get_user_by_email(email)
            if not user:
                return make_error_response(message="User not found!")

            login(request, user)
            refresh = RefreshToken.for_user(user)
            auth_data = {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }

            return Response(auth_data, status=status.HTTP_200_OK)

        else:
            return Response({"error": "Invalid request"}, status=status.HTTP_401_UNAUTHORIZED)
