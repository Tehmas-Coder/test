from django.db import transaction
from rest_framework import serializers

from apps.lookups.serializers.country_serializers import CountrySerializer
from apps.questionbank.serializers.media_serializers import MediaSerializer
from apps.user.models.user_models import BaseUser
from apps.user.serializers.role_permission_serializers import RoleSerializer
from utils.rna_utils import debug_print


class UserSerializer(serializers.ModelSerializer):
    """
    roles : List[Dicts]
    country : Dict (if context is not mutator)
    profile_picture : Dict (if context is not mutator)
    """

    class Meta:
        model = BaseUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "profile_picture",
            "roles",
            "country",
            "password",
            "phone",
            "otp",
            "is_verified",
            "is_superuser",
            "date_joined",
            "last_login",
            "description",
            "created_at",
            "updated_at",
            "meta_status",
        ]

        read_only_fields = [
            "id",
            "full_name",
            "is_verified",
            "is_superuser",
            "date_joined",
            "last_login",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    @transaction.atomic
    def create(self, validated_data):
        user = BaseUser.objects.create(**validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user

    def update(self, instance, validated_data):
        validated_data.pop("email", None)
        password = validated_data.pop("password", None)
        roles = self.initial_data.get("roles", None)  # type: ignore
        if password:
            instance.set_password(password)
        if roles:
            roles = list(eval(roles))
            instance.roles.set(roles)
        instance.save()
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        res = super().to_representation(instance)
        mutator_context = self.context.get("mutator", False)
        if not mutator_context:
            if res["country"]:
                res["country"] = CountrySerializer(instance.country).data
            if res["profile_picture"]:
                res["profile_picture"] = MediaSerializer(instance.profile_picture).data
        if res["roles"]:
            res["roles"] = RoleSerializer(instance.roles, many=True, context={"mutator": mutator_context}).data
        return res
