from cryptography.fernet import Fernet
from django.db.models import Q
from rest_framework import status, views, viewsets
from rest_framework.response import Response

from apps.exam_public.models.exam_public_models import CandidateExam
from apps.exam_scoring.custom.scoring_classes import CandidateExamScoring
from apps.exam_scoring.serializers.exam_report_serializers import ExamReportSerializer
from helpers.helper_functions import get_encryption_key
from utils.rna_utils import make_error_response


class CandidateExamScoringViewset(viewsets.ViewSet):

    # -------------------------- Candidate Exam Marking -------------------------- #

    def candidate_exam_marking(self, request, *args, **kwargs):
        candidate_exam_id = request.data.get("candidate_exam_id", None)
        request_data = request.data.get("questions_scores", None)
        if candidate_exam_id is None:
            return make_error_response(message="Candidate Exam id is required")
        if request_data is None:
            return make_error_response(message="Questions scores are required")
        response_data = CandidateExamScoring(candidate_exam_id).mark_candidate_exam(request_data)
        return Response({"message": response_data["message"]}, status=response_data["status"])

    # -------------------------- Candidate Exam Scoresheet -------------------------- #

    def candidate_exam_scoresheet(self, request, *args, **kwargs):
        candidate_exam_id = self.kwargs.get("id", None)
        try:
            candidate_exam_id = int(candidate_exam_id)
        except:
            try:
                token = candidate_exam_id[len("token=") :]
                key = get_encryption_key()
                cipher = Fernet(key)
                candidate_exam_id = int(cipher.decrypt(token).decode())
            except:
                return make_error_response(message="Invalid token")
        data = CandidateExamScoring(candidate_exam_id).get_candidate_exam_scoresheet()
        return Response(data, status=status.HTTP_200_OK)


class ExamReportAPIView(views.APIView):

    def post(self, request, *args, **kwargs):
        start_datetime = request.data.get("start_datetime", None)
        end_datetime = request.data.get("end_datetime", None)
        exam_id = request.data.get("exam_id", None)
        if start_datetime is None or end_datetime is None:
            return make_error_response(message="Start datetime and end datetime are required")
        if exam_id is None:
            return make_error_response(message="Exam id is required")
        candidate_exam_queryset = CandidateExam.get_detail_queryset(
            exam_backlog=True,
            candidate=True,
            q_filter=Q(exam_backlog__exam_id=exam_id, start_datetime__gte=start_datetime, end_datetime__lte=end_datetime),
        )
        report_data = ExamReportSerializer(candidate_exam_queryset, many=True).data
        return Response(report_data, status=status.HTTP_200_OK)
