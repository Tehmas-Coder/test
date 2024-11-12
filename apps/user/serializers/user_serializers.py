from django.db import transaction
from rest_framework import serializers

from apps.lookups.serializers.country_serializers import CountrySerializer
from apps.questionbank.serializers.media_serializers import MediaSerializer
from apps.user.models import BaseUser
from apps.user.serializers.role_permission_serializers import RoleSerializer
from utils.rna_utils import debug_print


class UserDetailSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)
    country = CountrySerializer(read_only=True)
    profile_picture = MediaSerializer(required=False)

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
            "email",
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "roles",
            "country",
            "phone",
            "is_verified",
            "is_superuser",
            "date_joined",
            "last_login",
            "created_at",
            "updated_at",
        ]


class UserEditSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True, context={"mutator": True})

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
            "otp",
            "full_name",
            "created_at",
            "is_verified",
            "updated_at",
            "is_superuser",
            "date_joined",
            "last_login",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def __init__(self, instance=None, data=..., **kwargs):
        context = kwargs.get("context", {})
        if context.get("is_update", False):
            self.Meta.fields.remove("roles")
        if data is not ...:
            super().__init__(instance, data, **kwargs)
        super().__init__(instance, **kwargs)

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
