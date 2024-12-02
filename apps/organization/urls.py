from django.urls import include, path
from rest_framework import routers

from apps.organization.views.organization_views import OrganizationRelatedViewset

router = routers.DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
    path(
        "get-organization-users-list/<int:id>/",
        OrganizationRelatedViewset.as_view({"get": "get_organization_users_list"}),
        name="get_orgaization_users_list",
    ),
    path(
        "get-organization-candidates-list/<int:id>/",
        OrganizationRelatedViewset.as_view({"get": "get_organization_candidates_list"}),
        name="get_organization_candidates_list",
    ),
    path(
        "get-candidate-organizations-list/",
        OrganizationRelatedViewset.as_view({"get": "get_candidate_organizations_list"}),
        name="get_candidate_organizations_list",
    ),
    path(
        "get-user-organizations-list/",
        OrganizationRelatedViewset.as_view({"get": "get_user_organizations_list"}),
        name="get_user_organizations_list",
    ),
]


urlpatterns += router.urls
