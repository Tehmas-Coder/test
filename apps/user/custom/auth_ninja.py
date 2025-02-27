import json

from cryptography.fernet import Fernet
from django.contrib.auth import login
from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.exam_public.models.exam_public_models import Candidate, CandidateExam
from apps.exam_public.serializers.candidate_exam_serializers import (
    CandidateExamListSerializer,
)
from apps.lookups.models.lookup_models import Country
from apps.user.models.user_models import BaseUser, Role
from apps.user.serializers.user_serializers import UserSerializer
from helpers.helper_functions import get_encryption_key
from middlewares.response_middleware import ResponseMiddleware
from utils.datetime_utils import convert_any_datetime_to_utc, get_current_utc_datetime
from utils.rna_utils import debug_print, generate_random_password, make_error_response


class AuthNinja:
    """
    AuthNinja class to handle the authentication and registration of users

    :Attributes:
    - `exam_token`: str: Exam token to decrypt
    - `request_data`: dict: Request data

    :Methods:
    - `register()`: Register the user based on the request data
    - `exam_token_handler(request)`: Handle the exam token and return the response data

    :Static Methods:
    - `create_candidate_with_exam_token`: Create candidate with exam token and return candidate exam instance
    - `decrypt_exam_token`: Decrypt the exam token
    """

    def __init__(self, exam_token, request_data) -> None:
        self.exam_token = exam_token
        self.request_data = request_data

    def register(self):
        response_data = {}
        if "is_superuser" in self.request_data:
            response_data = self.__register_superuser()
        else:
            response_data = self.__register_candidate()
        return response_data

    def exam_token_handler(self, request):
        """
        Handles the exam token and determines the appropriate response based on the token's data.

        This method decrypts the provided exam token and retrieves the associated user. Depending on the
        token's properties and the request data, it either handles a public exam token, directs the user
        to login/register, or processes an authenticated user's exam.

        Args:
            request (HttpRequest): The HTTP request object containing the request data.

        Returns:
            dict: A dictionary containing the response data, including the route and candidate exam data if applicable.
        """
        self.response_data = {}
        decrypted_data = AuthNinja.decrypt_exam_token(self.exam_token)
        self.user = BaseUser.objects.filter(email=decrypted_data["email"]).first()
        if decrypted_data["is_public"] or decrypted_data.get("is_student_apply_candidate"):
            self.__public_exam_token_handler(request, decrypted_data)
        else:
            if request.data.get("authentication_completed"):
                if not request.user.is_authenticated:
                    ResponseMiddleware.return_now(make_error_response(message="User is not authenticated"))
                candidate_exam_instance = AuthNinja.create_candidate_with_exam_token(self.user, decrypted_data)
                candidate_exam_data = CandidateExamListSerializer(candidate_exam_instance).data
                self.response_data["route"] = "exam"
                self.response_data["candidate_exam"] = candidate_exam_data
            else:
                self.response_data["route"] = "login" if self.user else "register"
        return self.response_data

    # ---------------------------------------------------------------------------- #
    #                                PRIVATE METHODS                               #
    # ---------------------------------------------------------------------------- #
    def __register_superuser(self):
        try:
            self.request_data["is_verified"] = True
            super_user_instance = BaseUser.objects.create_superuser(
                email=self.request_data.pop("email"), password=self.request_data.pop("password"), **self.request_data
            )  # type:ignore
            serializer = UserSerializer(super_user_instance, context={"mutator": True})
            return serializer.data
        except Exception as e:
            ResponseMiddleware.return_now(make_error_response(message=f"{str(e)}"))

    def __register_candidate(self):
        """
        Registers a new candidate user.

        This method performs the following steps:
        - Validates the user data using the UserSerializer.
        - Checks if the email already exists and handles existing users created in the "public_exam" context.
        - Saves the new user instance if validation passes.
        - Assigns the "Candidate" role to the user.
        - Creates a Candidate instance associated with the user.
        - Sends an OTP to the newly registered user.

        Returns:
            dict: Serialized data of the newly registered user.
        """
        serializer = UserSerializer(data=self.request_data, context={"mutator": False})
        if not serializer.is_valid():
            if "email" not in serializer.errors:
                ResponseMiddleware.return_now(Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST))
            user_instance = BaseUser.get_user_by_email(self.request_data.get("email"))
            if user_instance and user_instance.creation_context == "public_exam" and (not user_instance.otp):
                response_data = self.__update_already_created_user_from_public_exam(user_instance)
                ResponseMiddleware.return_now(Response(response_data, status=status.HTTP_201_CREATED))
            ResponseMiddleware.return_now(make_error_response(message="User with this email already exists"))
        user_instance = serializer.save()
        response_data = serializer.data
        # * Adding role to user
        role_id = Role.objects.filter(name__icontains="Candidate").values("id").first()
        user_instance.roles.add(role_id["id"])  # type:ignore
        # * Creating candidate instance
        if self.exam_token:
            decrypted_data = AuthNinja.decrypt_exam_token(self.exam_token)
            self.create_candidate_with_exam_token(user_instance, decrypted_data)
        else:
            Candidate.objects.create(user=user_instance)
        self.__send_otp_to_user(user_instance)
        return response_data

    def __send_otp_to_user(self, user_instance):
        if not user_instance.send_otp():
            transaction.set_rollback(True)
            ResponseMiddleware.return_now(make_error_response(message="Failed to send OTP, please try again"))

    def __update_already_created_user_from_public_exam(self, user_instance: BaseUser):
        user_instance.first_name = self.request_data.get("first_name")
        user_instance.last_name = self.request_data.get("last_name")
        user_instance.phone = self.request_data.get("phone")
        user_instance.set_password(self.request_data.get("password"))
        user_instance.creation_context = "self"
        user_instance.save()
        self.__send_otp_to_user(user_instance)
        return UserSerializer(user_instance).data

    def __public_exam_token_handler(self, request, decrypted_data):
        """
        Handles the public exam token for a user.

        This method performs the following steps:
        - Checks if the user is authenticated. If not, it fetches user data from the request.
        - If any required user data is missing, it returns a route to get the details.
        - Creates a new user with the provided email and user data, sets a random password, assigns the "Candidate" role, and saves the user.
        - Creates a candidate exam instance using the provided decrypted data.
        - Serializes the candidate exam data.
        - Logs in the user.
        - Generates and adds refresh and access tokens to the response data.
        - Sets the response route to "exam" and includes the candidate exam data.

        Args:
            request (HttpRequest): The HTTP request object.
            decrypted_data (dict): The decrypted data containing user and exam information.

        Returns:
            None
        """
        if not self.user:
            user_creation_required_data = self.__fetch_user_data_from_request()
            # * If any of the required data is missing, return the route to get the details
            if any(value is None for value in user_creation_required_data.values()):
                ResponseMiddleware.return_now(Response({"route": "get-details"}, status=status.HTTP_200_OK))
            self.user = BaseUser.objects.create(email=decrypted_data["email"], creation_context="public_exam", **user_creation_required_data)
            self.user.set_password(generate_random_password())
            role_id = Role.objects.filter(name__icontains="Candidate").values("id").first()
            self.user.roles.add(role_id["id"])  # type:ignore
            self.user.save()
        candidate_exam_instance = AuthNinja.create_candidate_with_exam_token(self.user, decrypted_data)
        candidate_exam_data = CandidateExamListSerializer(candidate_exam_instance).data
        login(request, self.user)
        refresh = RefreshToken.for_user(self.user)
        self.response_data["refresh"] = str(refresh)
        self.response_data["access"] = str(refresh.access_token)  # type: ignore
        self.response_data["route"] = "exam"
        self.response_data["candidate_exam"] = candidate_exam_data

    def __fetch_user_data_from_request(self) -> dict:
        user_creation_required_data = {
            "first_name": self.request_data.get("first_name"),
            "last_name": self.request_data.get("last_name"),
            "country_id": self.__get_country_id(self.request_data.get("country")),
        }
        return user_creation_required_data

    def __get_country_id(self, country):
        try:
            return int(country) if country.isdigit() else Country.objects.get(name__icontains=country).pk
        except:
            return None

    # ---------------------------------------------------------------------------- #
    #                                STATIC METHODS                               #
    # ---------------------------------------------------------------------------- #
    @staticmethod
    def create_candidate_with_exam_token(user_instance, decrypted_data):
        """
        Associates the user with a candidate instance and updates the candidate exam.

        This method checks if the user is already registered as a candidate. If not, it creates a candidate instance
        for the user with the organization provided in the decrypted data. It then updates the candidate exam with
        the candidate instance.

        Args:
            user_instance (BaseUser): The user instance to associate with the candidate.
            decrypted_data (dict): The decrypted data from the exam token.

        Returns:
            CandidateExam (CandidateExam): The candidate exam instance associated with the user.
        """
        organization_id = decrypted_data["organization_id"]
        candidate_exam_id = decrypted_data["candidate_exam_id"]
        candidate_instance, _ = Candidate.objects.get_or_create(user=user_instance, organization_id=organization_id)
        candidate_exam = CandidateExam.get_detail_queryset(candidate=True, exam_backlog=True, q_filter=Q(id=candidate_exam_id))
        candidate_exam.update(candidate=candidate_instance)
        return candidate_exam.first()

    @staticmethod
    def decrypt_exam_token(token):
        """
        Decrypts the provided exam token.

        This method decrypts the provided token using the encryption key and returns the decrypted data.
        If the token is invalid or expired, it returns an error response.

        Args:
            token (str): The encrypted exam token.

        Returns:
            dict: The decrypted data from the token.
        """
        key = get_encryption_key()
        cipher = Fernet(key)
        try:
            decrypted_data = json.loads(cipher.decrypt(token).decode())
            link_expiry_datetime = decrypted_data.get("end_datetime")
            if link_expiry_datetime and convert_any_datetime_to_utc(link_expiry_datetime) < get_current_utc_datetime():
                ResponseMiddleware.return_now(make_error_response(message="Link has expired"))
        except:
            ResponseMiddleware.return_now(make_error_response(message="Invalid Token"))
        return decrypted_data
