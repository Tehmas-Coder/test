from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models import BaseUser
from utils.db_utils import create_seed_from_db


class TempApi(APIView):
    def get(self, request):
        res = create_seed_from_db(BaseUser)
        return Response(res)
