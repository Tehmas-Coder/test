import json
from abc import ABC, abstractmethod

from django.db.models import F
from rest_framework import status
from rest_framework.response import Response

from apps.organization.models.organization_models import OrganizationPackage
from apps.questionbank.serializers.question_serializers.question_serializers import (
    QuestionDetailSerializer,
)
from apps.user.utils.utils import get_current_user_organization
from middlewares.current_user_middleware import get_current_user
from middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import debug_print, make_error_response


class MediaExtractor(ABC):
    @abstractmethod
    def extract(self, request, media_keys):
        pass


class DefaultMediaExtractor(MediaExtractor):
    def extract(self, request, media_keys):
        medias = []
        for key in media_keys:
            file = request.FILES.get(key)
            if file:
                medias.append({"file": file})
        return medias


class HintMediaExtractor(DefaultMediaExtractor):
    def extract_media(self, request, hints):
        for hint in hints:
            hint["medias"] = self.extract(request, hint.get("medias", []))
        return hints


class ChoiceMediaExtractor(DefaultMediaExtractor):
    def extract_media(self, request, choices):
        for choice in choices:
            choice["medias"] = self.extract(request, choice.get("medias", []))
        return choices


class RequestParser:
    def __init__(self, media_extractor: MediaExtractor) -> None:
        self.media_extractor = media_extractor

    def parse(self, request):
        if "data" in request.data:
            return self.parse_media(request)
        return request.data

    def parse_media(self, request):
        request_data = json.loads(request.data["data"])

        # * Extract media for questions
        media_keys = request_data.pop("medias", [])
        request_data["medias"] = self.media_extractor.extract(request, media_keys)

        hint_media_extractor = HintMediaExtractor()
        request_data["retry_hints"] = hint_media_extractor.extract_media(request, request_data.get("retry_hints", []))

        choice_media_extractor = ChoiceMediaExtractor()
        request_data["choices"] = choice_media_extractor.extract_media(request, request_data.get("choices", []))

        return request_data


class QuestionVisibilitySetter:
    @staticmethod
    def set_visibility(request_data):
        if get_current_user().is_superuser:  # type: ignore
            request_data["is_public"] = 1
        else:
            request_data["is_public"] = 0
        return request_data


class OrganizationValidator:
    @staticmethod
    def validate_user_organization():
        organization_id = get_current_user_organization()
        if not organization_id:
            raise ValueError("User doesn't belong to any organization")
        return organization_id

    @staticmethod
    def validate_organization_package(organization_id):
        organization_package = (
            OrganizationPackage.objects.filter(organization_id=organization_id).annotate(total_questions=F("package__questions")).last()
        )
        if not (organization_package.questions <= organization_package.total_questions):  # type:ignore
            raise ValueError("Your limit to create questions is reached")
        organization_package.questions += 1  # type:ignore
        organization_package.save()  # type:ignore
        return organization_id


class QuestionService:
    def __init__(
        self,
        request_parser: RequestParser,
        visibility_setter: QuestionVisibilitySetter,
        organization_validator: OrganizationValidator,
        serializer_class,
    ):
        self.request_parser = request_parser
        self.visibility_setter = visibility_setter
        self.organization_validator = organization_validator
        self.serializer_class = serializer_class

    def create_question(self, request):
        request_data = self.request_parser.parse(request)
        request_data = self.visibility_setter.set_visibility(request_data)

        if not get_current_user().is_superuser:  # type: ignore
            try:
                organization_id = self.organization_validator.validate_user_organization()
                self.organization_validator.validate_organization_package(organization_id)
                request_data["organization"] = organization_id
            except ValueError as e:
                ResponseMiddleware.return_now(make_error_response(message=f"Failed: {str(e)}"))

        serializer = self.serializer_class(data=request_data)
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        response_data = QuestionDetailSerializer(question).data
        return Response(response_data, status=status.HTTP_201_CREATED)
