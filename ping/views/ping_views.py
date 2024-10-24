from typing import Any
from rest_framework.response import Response
from rest_framework import views, status
from utils.rna_utils import print_test_header


class PingAPI(views.APIView):

    def get(self, request):

        return Response(
            data={"Status": "success", "Message": "pong"}, status=status.HTTP_200_OK
        )
