from core.serializers import BaseModelSerializer, get_base_model_fields
from apps.user.models import Resource


class ResourceSerializer(BaseModelSerializer):
    class Meta:
        model = Resource
        fields = ["id", "name", "regex", "method"] + get_base_model_fields()
