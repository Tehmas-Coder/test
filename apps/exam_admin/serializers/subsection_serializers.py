from apps.exam_admin.models.exam_admin_models import SubSection
from core.serializers import BaseModelSerializer, get_base_model_fields


class SubSectionSerializer(BaseModelSerializer):

    class Meta:
        model = SubSection
        fields = [
            "id",
            "section",
            "measuring_unit",
            "title",
            "sequence",
            "time_limit",
            "is_global",
            "is_shuffle",
        ] + get_base_model_fields()

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if not self.context.get("include_section", False):
            rep.pop("section")
        return rep
