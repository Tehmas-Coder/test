from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.lookups.serializers.country_serializers import CountrySerializer
from apps.lookups.serializers.media_serializers import MediaSerializer
from apps.user.models import BaseUser
from apps.user.serializers.role_permission_serializers import RoleSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields
from utils.rna_utils import color_print, debug_print


class UserDetailSerializer(BaseModelSerializer):
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
        ] + get_base_model_fields()

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
        ]


class UserEditSerializer(BaseModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)

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
        ] + get_base_model_fields()

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
        if password:
            instance.set_password(password)
        instance.save()
        return super().update(instance, validated_data)


class LoginSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super(TokenObtainPairSerializer, cls).get_token(user)

        token["username"] = user.email
        token["full_name"] = user.full_name
        token["email"] = user.email
        token["is_superuser"] = user.is_superuser

        return token
