from django.urls import include, path
from rest_framework import routers

from apps.organization.views import OrganizationRelatedViewset, OrganizationViewSet

router = routers.DefaultRouter()
router.register(r"organizations", OrganizationViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "get_orgaization_users_list/",
        OrganizationRelatedViewset.as_view({"get": "get_orgaization_users_list"}),
        name="get_orgaization_users_list",
    ),
    path(
        "get_orgaization_candidates_list/<int:id>/",
        OrganizationRelatedViewset.as_view({"get": "get_orgaization_candidates_list"}),
        name="get_orgaization_candidates_list",
    ),
]

urlpatterns += router.urls
