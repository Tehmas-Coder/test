from django.db import models

from apps.organization.models.organization_models import Organization
from core.models import BaseModel

MEDIA_MODEL = "lookups.Media"


class Candidate(BaseModel):
    user = models.ForeignKey("user.BaseUser", on_delete=models.CASCADE, related_name="user_candidates")
    organization = models.ForeignKey(to=Organization, on_delete=models.CASCADE, null=True, blank=True, related_name="organization_candidates")

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_candidate"


class CandidateExam(BaseModel):
    candidate = models.ForeignKey("exam_public.Candidate", on_delete=models.CASCADE, null=True, blank=True)
    candidate_email = models.EmailField()
    exam_backlog = models.ForeignKey("exam_public.ExamBacklog", on_delete=models.CASCADE, related_name="candiate_exam_examsbacklog")
    schedule = models.ForeignKey("exam_admin.Schedule", on_delete=models.CASCADE)
    obtained_marks = models.PositiveIntegerField(default=0)

    # ? To be filled from schedule
    date = models.DateField(auto_now=False, auto_now_add=False)
    start_time = models.TimeField(auto_now=False, auto_now_add=False, null=True)
    end_time = models.TimeField(auto_now=False, auto_now_add=False, null=True)
    waiting_duration = models.PositiveIntegerField(null=True)
    extra_duration = models.PositiveIntegerField(null=True)

    is_preparatory = models.BooleanField(default=False)

    class Meta:
        app_label = "exam_public"


class CandidateExamAnswer(BaseModel):
    candidate_exam = models.ForeignKey("exam_public.CandidateExam", on_delete=models.CASCADE, related_name="exam_answers")
    exam_backlog_question = models.ForeignKey("exam_public.ExamBacklogQuestion", on_delete=models.CASCADE, related_name="question_answers")
    exam_backlog_question_choice = models.ForeignKey("exam_public.ExamBacklogQuestionChoice", on_delete=models.CASCADE, null=True, blank=True)

    answer_text = models.TextField(null=True, blank=True)
    answer_files = models.ManyToManyField(MEDIA_MODEL, through="exam_public.CandidateExamAnswerMedia")

    score = models.FloatField(default=0)
    seconds_taken = models.IntegerField(default=0)

    is_scored = models.BooleanField(default=False)
    is_correct = models.BooleanField(default=False)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_candidateexam_answer"


# ---------------------------------------------------------------------------- #
#                                   MAPPINGS                                   #
# ---------------------------------------------------------------------------- #


class CandidateExamAnswerMedia(BaseModel):
    candidate_exam_answer = models.ForeignKey(CandidateExamAnswer, on_delete=models.CASCADE)
    media = models.ForeignKey(MEDIA_MODEL, on_delete=models.CASCADE)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_candidateexam_answer_media"
