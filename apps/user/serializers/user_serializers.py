from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.user.models import BaseUser
from apps.user.serializers.role_serializers import RoleSerializer


class UserDetailSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)

    class Meta:
        model = BaseUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "roles",
            "password",
            "is_active",
            "phone",
            "is_verified",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "meta_status",
        ]
        read_only_fields = [
            "id",
            "full_name",
            "created_at",
            "is_verified",
            "updated_at",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = BaseUser.objects.create(**validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == "password":
                instance.set_password(value)
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance


class LoginSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super(TokenObtainPairSerializer, cls).get_token(user)

        token["username"] = user.email
        token["email"] = user.email
        token["is_staff"] = user.is_staff
        token["is_superuser"] = user.is_superuser

        return token
