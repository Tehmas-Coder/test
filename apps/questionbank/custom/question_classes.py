import json
from abc import ABC, abstractmethod

from rest_framework import status
from rest_framework.response import Response

from apps.organization.models.organization_models import OrganizationPackage
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
    def extract(self, request, media_keys: list):
        medias = []
        for key in media_keys:
            file = request.FILES.get(key)
            if file:
                medias.append({"file": file})
        return medias


class HintMediaExtractor(DefaultMediaExtractor):
    def extract(self, request, hints: list):
        for hint in hints:
            hint["medias"] = super().extract(request, hint.get("medias", []))
        return hints


class ChoiceMediaExtractor(DefaultMediaExtractor):
    def extract(self, request, choices: list):
        for choice in choices:
            choice["medias"] = super().extract(request, choice.get("medias", []))
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

        # * Extract medias for question, its choices and hints
        media_keys = request_data.pop("medias", [])
        request_data["medias"] = self.media_extractor.extract(request, media_keys)
        request_data["retry_hints"] = HintMediaExtractor().extract(request, request_data.get("retry_hints", []))
        request_data["choices"] = ChoiceMediaExtractor().extract(request, request_data.get("choices", []))

        return request_data


class VisibilitySetter:
    def set_visibility(self, request_data: dict):
        if get_current_user().is_superuser:  # type: ignore
            request_data["is_public"] = 1
        else:
            request_data["is_public"] = 0
        return request_data


class QuestionVisibilitySetter(VisibilitySetter):
    def set_visibility(self, request_data: dict):
        return super().set_visibility(request_data)


class OrganizationValidator:
    def __init__(self, organization_id=None) -> None:
        if (organization_id is None) and (not get_current_user().is_superuser):  # type: ignore
            organization_id = get_current_user_organization()
        self.organization_id = organization_id

    def validate(self):
        return self.organization_id


class OrganizationPackageLimitValidator(OrganizationValidator):
    def __init__(self, organization_id=None) -> None:
        super().__init__(organization_id)
        self.organization_package = OrganizationPackage.objects.filter(organization_id=self.organization_id).select_related("package").last()

    def validate(self):
        return super().validate()

    def validate_limit(self, current_count, total_limit):
        if not (current_count <= total_limit):
            raise ValueError("Package limit for this action has been reached")
        current_count += 1
        return current_count

    def save_organization_package(self):
        self.organization_package.save()  # type: ignore


class OrganizationPackageQuestionLimitValidator(OrganizationPackageLimitValidator):
    def validate(self):
        try:
            self.organization_package.questions = self.validate_limit(self.organization_package.questions, self.organization_package.package.questions)  # type: ignore
            self.save_organization_package()
            return self.organization_id
        except ValueError as e:
            raise ValueError(str(e))


class QuestionService:
    def __init__(
        self,
        request_parser: RequestParser,
        visibility_setter: VisibilitySetter,
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

        serializer = self.serializer_class(data=request_data)
        serializer.is_valid(raise_exception=True)

        if not get_current_user().is_superuser:  # type: ignore
            try:
                organization_id = OrganizationPackageQuestionLimitValidator().validate()
                request_data["organization"] = organization_id  # type: ignore
            except ValueError as e:
                ResponseMiddleware.return_now(make_error_response(message=f"Failed: {str(e)}"))

        question = serializer.save()
        response_data = QuestionDetailSerializer(question).data
        return Response(response_data, status=status.HTTP_201_CREATED)
