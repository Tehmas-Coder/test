from rest_framework.views import APIView
from utils.db_utils import create_seed_from_db
from apps.lookups.models import Country, Region, Timezone
from rest_framework.response import Response
from utils.rna_utils import debug_print


class TempApi(APIView):
    def get(self, request):
        res = create_seed_from_db(Country)
        return Response(res)
