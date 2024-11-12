import json

from cryptography.fernet import Fernet
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

from apps.exam_public.models.exam_public_models import Candidate, CandidateExam
from apps.user.serializers.user_serializers import LoginSerializer, UserEditSerializer
from utils.rna_utils import (
    debug_print,
    get_encryption_key,
    make_error_response,
    make_success_response,
)

from ..models import BaseUser, Role


class RegisterApiView(views.APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        token_data = request.query_params.get("token", None)
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
                user_instance = serializer.save()
                role_id = Role.objects.filter(name__icontains="Candidate").values("id").first()
                user_instance.roles.add(role_id["id"])  # type:ignore
                if not user_instance.send_otp():  # type:ignore
                    transaction.set_rollback(True)
                    raise serializers.ValidationError({"error": "Failed to send email, please try again"})

                # * This if block code is for user registration on exam attempt and this token is generated from exam API
                if token_data is not None:
                    key = get_encryption_key()
                    cipher = Fernet(key)
                    decrypted_data = json.loads(cipher.decrypt(token_data).decode())
                    organization_id = decrypted_data["organization_id"]
                    candidate_exam_id = decrypted_data["candidate_exam_id"]
                    if organization_id:
                        candidate_instance = Candidate.objects.create(user=user_instance, organization_id=organization_id)
                    else:
                        candidate_instance = Candidate.objects.create(user=user_instance)

                    CandidateExam.objects.filter(id=candidate_exam_id).update(candidate=candidate_instance)
                else:
                    Candidate.objects.create(user=user_instance)
                return Response(serializer.data, status=201)
            if "email" in serializer.errors:
                return Response({"error": "User with this email already exists"}, status=400)
            return Response(serializer.errors, status=400)


class LoginApiView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get("email", None)  # type: ignore
        token_data = request.query_params.get("token", None)
        if not email:
            return make_error_response(message="Email is required!")
        user = BaseUser.get_user_by_email(email)
        if not user:
            return make_error_response(message="User not found!")

        # * This token data is for candidate user creation on exam attempt and is generated from exam API
        if token_data is not None:
            key = get_encryption_key()
            cipher = Fernet(key)
            decrypted_data = json.loads(cipher.decrypt(token_data).decode())
            organization_id = decrypted_data["organization_id"]
            candidate_exam_id = decrypted_data["candidate_exam_id"]
            candidate_instance, _ = Candidate.objects.get_or_create(user=user, organization_id=organization_id)
            CandidateExam.objects.filter(id=candidate_exam_id).update(candidate=candidate_instance)

        user_role_name = None
        if "is_system_user" in request.data:  # type: ignore
            user_role_name = user.roles.all().values().first()

        if user_role_name == None:
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
    USER_NOT_FOUND = {"error": "User not found!"}

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


class SaToQBLoginApiView(TokenObtainPairView):

    def post(self, request):

        if "is_system_user" in request.data:
            email = request.data.get("email", None)

            if not email:
                return make_error_response(message="Email is required!")
            user = BaseUser.get_user_by_email(email)
            if not user:
                return make_error_response(message="User not found!")

            login(request, user)
            refresh = RefreshToken.for_user(user)
            auth_data = {
                "refresh": str(refresh),
                "access": str(refresh.access_token),  # type: ignore
            }

            return Response(auth_data, status=status.HTTP_200_OK)

        else:
            return Response({"error": "Invalid request"}, status=status.HTTP_401_UNAUTHORIZED)
