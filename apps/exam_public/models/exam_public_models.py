from django.db import models

from apps.exam_public.helpers.queryset_functions import (
    get_candidate_detailed_queryset,
    get_candidate_exam_detailed_queryset,
)
from core.models import BaseModel

MEDIA_MODEL = "user.Media"


class Candidate(BaseModel):
    user = models.ForeignKey("user.BaseUser", on_delete=models.CASCADE, related_name="user_candidates")
    organization = models.ForeignKey("lookups.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="organization_candidates")

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_candidate"

    @classmethod
    def get_detail_queryset(cls, organization=False, user=False) -> models.QuerySet:
        return get_candidate_detailed_queryset(cls, organization, user)


class CandidateExam(BaseModel):
    candidate = models.ForeignKey("exam_public.Candidate", on_delete=models.CASCADE, null=True, blank=True)
    exam_backlog = models.ForeignKey("exam_public.ExamBacklog", on_delete=models.CASCADE, related_name="candidate_exam_examsbacklog")
    schedule = models.ForeignKey("exam_admin.Schedule", on_delete=models.CASCADE)

    candidate_email = models.EmailField()
    total_obtainable_marks = models.FloatField(null=True, blank=True)
    obtained_marks = models.FloatField(null=True, blank=True)
    exam_duration = models.PositiveIntegerField(null=True)

    EXAM_STATUS_CHOICES = (
        ("assigned", "Assigned"),
        ("attempted", "Attempted"),
        ("submitted", "Submitted"),
        ("marked", "Marked"),
        ("scored", "Scored"),
    )

    exam_status = models.CharField(max_length=100, choices=EXAM_STATUS_CHOICES, default="assigned")

    # ? To be filled from schedule
    start_datetime = models.DateTimeField(auto_now=False, auto_now_add=False)
    end_datetime = models.DateTimeField(auto_now=False, auto_now_add=False)
    waiting_duration = models.PositiveIntegerField(null=True)
    extra_duration = models.PositiveIntegerField(null=True)

    is_preparatory = models.BooleanField(default=False)

    class Meta:
        app_label = "exam_public"

    @classmethod
    def get_detail_queryset(cls, exam_backlog=False, schedule=False, candidate=False) -> models.QuerySet:
        return get_candidate_exam_detailed_queryset(cls, exam_backlog, schedule, candidate)


class CandidateExamStatusLog(BaseModel):
    candidate_exam = models.ForeignKey("exam_public.CandidateExam", on_delete=models.CASCADE, related_name="status_logs")
    exam_status = models.CharField(max_length=100)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_candidateexam_statuslog"


class CandidateExamAnswer(BaseModel):
    candidate_exam = models.ForeignKey("exam_public.CandidateExam", on_delete=models.CASCADE, related_name="exam_answers")
    exam_backlog_question = models.ForeignKey("exam_public.ExamBacklogQuestion", on_delete=models.CASCADE, related_name="question_answers")
    exam_backlog_question_choice = models.ForeignKey("exam_public.ExamBacklogQuestionChoice", on_delete=models.CASCADE, null=True, blank=True)

    exam_backlog_question_choice_title = models.TextField(null=True, blank=True)
    answer_text = models.TextField(null=True, blank=True)
    score = models.FloatField(blank=True, null=True)
    seconds_taken = models.IntegerField(default=0)

    is_attempted = models.BooleanField(default=True)
    is_correct = models.BooleanField(default=False)

    answer_files = models.ManyToManyField(MEDIA_MODEL, through="exam_public.CandidateExamAnswerMedia")

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


class CandidateExamRetryhint(BaseModel):
    candidate_exam = models.ForeignKey("exam_public.CandidateExam", on_delete=models.CASCADE, related_name="candidate_exam_retry_hints")
    exam_backlog_question_retry_hint = models.ForeignKey("exam_public.ExamBacklogQuestionRetryHint", on_delete=models.CASCADE)
    exam_backlog_question = models.ForeignKey(
        "exam_public.ExamBacklogQuestion", on_delete=models.CASCADE, related_name="question_fetched_retry_hints"
    )

    penalty_score = models.DecimalField(max_digits=10, decimal_places=1)

    def save(self, *args, **kwargs):
        self.penalty_score = (self.exam_backlog_question.retry_penalty / 100) * self.exam_backlog_question.total_marks
        return super().save(*args, **kwargs)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_candidateexam_retryhint"
