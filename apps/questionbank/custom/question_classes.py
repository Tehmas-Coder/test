import json

from django.db.models import F
from rest_framework import status
from rest_framework.response import Response

from apps.lookups.models import Organization
from apps.organization.models.organization_models import (
    OrganizationPackage,
    OrganizationUser,
)
from apps.questionbank.serializers.question_serializers.question_serializers import (
    QuestionDetailSerializer,
)
from middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import make_error_response


class RequestParser:
    @staticmethod
    def parse(request):
        if "data" in request.data:
            return RequestParser.parse_media(request)
        return request.data

    @staticmethod
    def parse_media(request):
        request_data = json.loads(request.data["data"])

        # * Extract media for questions
        media_keys = request_data.pop("medias", [])
        request_data["medias"] = []
        for key in media_keys:
            file = request.FILES.get(key)
            if file:
                request_data["medias"].append(
                    {
                        "file": file,
                    }
                )

        # * Extract media for hints
        for hint in request_data.get("retry_hints", []):
            hint_medias = hint.pop("medias", [])
            if hint["has_media"]:
                hint["medias"] = []
                for key in hint_medias:
                    file = request.FILES.get(key)
                    if file:
                        hint["medias"].append(
                            {
                                "file": file,
                            }
                        )

        # * Extract media for choices
        for choice in request_data.get("choices", []):
            choice_medias = choice.pop("medias", [])
            if choice["has_media"]:
                choice["medias"] = []
                for key in choice_medias:
                    file = request.FILES.get(key)
                    if file:
                        choice["medias"].append(
                            {
                                "file": file,
                            }
                        )

        return request_data


class QuestionVisibilitySetter:
    @staticmethod
    def set_visibility(request, request_data):
        if request.user.is_superuser:
            request_data["is_public"] = 1
        else:
            request_data["is_public"] = 0
        return request_data


class OrganizationValidator:
    @staticmethod
    def validate_user_organization(request):
        organization_id = OrganizationUser.objects.filter(user_id=request.user.id).values_list("organization", flat=True).first()
        if not organization_id:
            raise ValueError("User doesn't belong to any organization")
        return organization_id

    @staticmethod
    def validate_organization_package(organization_id):
        organization = Organization.objects.get(id=organization_id)
        organization_package = OrganizationPackage.objects.filter(organization=organization).annotate(total_questions=F("package__questions")).last()
        if not (organization_package.questions <= organization_package.total_questions):  # type:ignore
            raise ValueError("Your limit to create questions is reached")
        organization_package.questions += 1  # type:ignore
        organization_package.save()  # type:ignore
        return organization_id


class QuestionService:
    def __init__(self, request_parser, visibility_setter, organization_validator, serializer_class):
        self.request_parser = request_parser
        self.visibility_setter = visibility_setter
        self.organization_validator = organization_validator
        self.serializer_class = serializer_class

    def create_question(self, request):
        request_data = self.request_parser.parse(request)
        request_data = self.visibility_setter.set_visibility(request, request_data)

        if not request.user.is_superuser:
            try:
                organization_id = self.organization_validator.validate_user_organization(request)
                self.organization_validator.validate_organization_package(organization_id)
                request_data["organization"] = organization_id
            except ValueError as e:
                ResponseMiddleware.return_now(make_error_response(message=f"Failed: {str(e)}"))

        serializer = self.serializer_class(data=request_data)
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        response_data = QuestionDetailSerializer(question).data
        return Response(response_data, status=status.HTTP_201_CREATED)
