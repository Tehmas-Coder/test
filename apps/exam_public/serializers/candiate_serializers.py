from apps.exam_public.models.exam_public_models import Candidate
from apps.user.serializers.user_serializers import UserDetailSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields


class CandidateSerializer(BaseModelSerializer):

    class Meta:
        model = Candidate
        fields = [
            "id",
            "user",
        ] + get_base_model_fields()


class CandidateDetailSerializer(BaseModelSerializer):
    user = UserDetailSerializer(required=True)

    class Meta:
        model = Candidate
        fields = [
            "id",
            "user",
        ] + get_base_model_fields()
