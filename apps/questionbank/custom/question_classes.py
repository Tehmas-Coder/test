import json
from abc import ABC, abstractmethod

from rest_framework import status
from rest_framework.response import Response

from apps.lookups.custom.lookups_classes import (
    OrganizationPackageLimitValidator,
    OrganizationValidator,
    VisibilitySetter,
)
from apps.questionbank.serializers.question_serializers.question_serializers import (
    QuestionDetailSerializer,
)
from apps.user.utils.utils import get_current_user_organization
from middlewares.current_user_middleware import get_current_user
from middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import color_print, debug_print, make_error_response


class MediaExtractor(ABC):
    @abstractmethod
    def extract(self, request, media_keys):
        pass


class DefaultMediaExtractor(MediaExtractor):
    """
    This class is used to extract the media files from the request.
    """

    def extract(self, request, media_keys: list) -> list:
        medias = []
        for key in media_keys:
            file = request.FILES.get(key)
            if file:
                medias.append({"file": file})
        return medias


class HintMediaExtractor(DefaultMediaExtractor):
    """
    This class is used to extract the media files from the hints of the question.
    """

    def extract(self, request, hints: list) -> list:
        for hint in hints:
            hint["medias"] = super().extract(request, hint.get("medias", []))
        return hints


class ChoiceMediaExtractor(DefaultMediaExtractor):
    """
    This class is used to extract the media files from the choices of the question.
    """

    def extract(self, request, choices: list) -> list:
        for choice in choices:
            choice["medias"] = super().extract(request, choice.get("medias", []))
        return choices


class RequestParser:
    """
    This class is used to parse the request data and extract the media files from the request.
    """

    def __init__(
        self,
        media_extractor: MediaExtractor = DefaultMediaExtractor(),
        fetch_default_media=True,
        fetch_hint_medias=False,
        fetch_choice_medias=False,
    ) -> None:
        self.media_extractor = media_extractor
        self.fetch_default_media = fetch_default_media
        self.fetch_hint_medias = fetch_hint_medias
        self.fetch_choice_medias = fetch_choice_medias

    def parse(self, request) -> dict:
        return self.parse_media(request) if "data" in request.data else request.data

    def parse_media(self, request) -> dict:
        request_data = json.loads(request.data["data"])

        if self.fetch_default_media:
            request_data["medias"] = self.media_extractor.extract(request, request_data.pop("medias", []))
        if self.fetch_hint_medias:
            request_data["retry_hints"] = HintMediaExtractor().extract(request, request_data.get("retry_hints", []))
        if self.fetch_choice_medias:
            request_data["choices"] = ChoiceMediaExtractor().extract(request, request_data.get("choices", []))

        return request_data


class QuestionVisibilitySetter(VisibilitySetter):
    """
    This class is used to set the visibility of the question to public or non public based on the user's role.
    """

    def set_visibility(self, request_data: dict) -> dict:
        return super().set_visibility(request_data)


class OrganizationPackageQuestionLimitValidator(OrganizationPackageLimitValidator):
    """
    This class is used to validate the question creation package limits of the organization.
    """

    def __init__(self, organization_id=None) -> None:
        super().__init__(organization_id)

    def validate(self) -> bool:
        try:
            self.organization_package.questions = self.validate_limit(self.organization_package.questions, self.organization_package.package.questions)  # type: ignore
            self.save_organization_package()
            return True
        except ValueError as e:
            raise ValueError(str(e))


class QuestionService:
    """
    This class is used to perfrom question CRUD operations.
    """

    def __init__(
        self,
        request_parser: RequestParser,
        visibility_setter: VisibilitySetter,
        serializer_class,
    ) -> None:
        self.request_parser = request_parser
        self.visibility_setter = visibility_setter
        self.serializer_class = serializer_class

    def create_question(self, request) -> Response:
        request_data = self.request_parser.parse(request)
        request_data = self.visibility_setter.set_visibility(request_data)

        serializer = self.serializer_class(data=request_data)
        serializer.is_valid(raise_exception=True)

        if not get_current_user().is_superuser:  # type: ignore
            try:
                organization_id = get_current_user_organization()
                OrganizationPackageQuestionLimitValidator(organization_id=organization_id).validate()
                request_data["organization"] = organization_id  # type: ignore
            except ValueError as e:
                ResponseMiddleware.return_now(make_error_response(message=f"Failed: {str(e)}"))

        question = serializer.save()
        response_data = QuestionDetailSerializer(question).data
        return Response(response_data, status=status.HTTP_201_CREATED)
