from rest_framework import status, views
from rest_framework.response import Response


class PingAPI(views.APIView):

    def get(self, request):

        return Response(data={"Status": "success", "Message": "pong"}, status=status.HTTP_200_OK)
