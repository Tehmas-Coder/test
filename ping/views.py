from typing import Any

from rest_framework import status, views
from rest_framework.response import Response

from utils.rna_utils import print_test_header


class PingAPI(views.APIView):

    def get(self, request):

        return Response(data={"Status": "success", "Message": "pong to ponga"}, status=status.HTTP_200_OK)
