from rest_framework.views import APIView
from utils.db_utils import create_seed_from_db
from apps.lookups.models import Country, Region, Timezone
from rest_framework.response import Response
from utils.rna_utils import debug_print
from apps.questionbank.models import Question
from apps.questionbank.serializers.question_serializers import QuestionDetailSerializer


class TempApi(APIView):
    def get(self, request):
        res = QuestionDetailSerializer(
            Question.get_questions_for_countries([1, 2]), many=True
        ).data
        return Response(res)
