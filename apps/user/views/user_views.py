from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.user.filters.user_filter import UserFilter
from apps.user.serializers.user_serializers import (
    UserDetailSerializer,
    UserEditSerializer,
)

from ..models import BaseUser

# ---------------------------------------------------------------------------- #
#                                     USER                                     #
# ---------------------------------------------------------------------------- #


class UserViewSet(viewsets.ModelViewSet):
    queryset = BaseUser.objects.all()
    serializer_class = UserDetailSerializer
    filterset_class = UserFilter
    USER_NOT_FOUND = {"error": "User not found"}
    USER_STATUSES = ["active", "inactive", "deleted"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return UserEditSerializer

        return super().get_serializer_class()

    def get_object(self, id: int | None = None):
        try:
            return BaseUser.objects.get(pk=id or self.kwargs.get("pk"))
        except BaseUser.DoesNotExist:
            return None

    # ------------------------------------ API ----------------------------------- #

    def list(self, request, *args, **kwargs):
        self.queryset = self.queryset.filter(meta_status="active")
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        request.data["is_staff"] = True
        request.data["is_superuser"] = False
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        if "email" in serializer.errors:
            return Response({"error": "User with this email already exists"}, status=400)
        return Response(serializer.errors, status=400)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object(id=kwargs.get("pk"))
        if not instance:
            return Response(self.USER_NOT_FOUND, status=404)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object(id=kwargs.get("pk"))
        if not instance:
            return Response({"error": "User not found"}, status=404)
        instance.deactivate()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def restore(self, request, *args, **kwargs):
        instance = self.get_object(id=kwargs.get("pk"))
        if not instance:
            return Response(self.USER_NOT_FOUND, status=404)
        instance.activate()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="bulk-delete")
    def bulk_delete(self, request):
        user_ids = request.data.get("users", [])
        users = BaseUser.objects.filter(id__in=user_ids)
        for user in users:
            user.delete()
        return Response({"status": "deleted", "message": "Users deleted!"})
