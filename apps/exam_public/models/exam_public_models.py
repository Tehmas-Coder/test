from django.db import models

from apps.exam_public.helpers.queryset_functions import (
    get_candidate_detailed_queryset,
    get_candidate_exam_detailed_queryset,
)
from apps.user.utils.utils import get_current_user_organization
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
    schedule = models.ForeignKey("exam_admin.Schedule", on_delete=models.CASCADE, null=True, blank=True)
    organization = models.ForeignKey("lookups.Organization", on_delete=models.CASCADE, null=True, blank=True)

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
        ("expired", "Expired"),
    )
    EXAM_RESULT_CHOICES = (
        ("pass", "Pass"),
        ("fail", "Fail"),
        ("pending", "Pending"),
    )
    EXAM_QUESTIONS_VISIBILITY_CHOICES = (
        ("all_at_once", "All at Once"),
        ("one_by_one", "One by One"),
    )
    exam_status = models.CharField(max_length=100, choices=EXAM_STATUS_CHOICES, default="assigned")
    exam_result = models.CharField(max_length=100, choices=EXAM_RESULT_CHOICES, default="pending")
    exam_questions_visibility = models.CharField(max_length=100, choices=EXAM_QUESTIONS_VISIBILITY_CHOICES, default="all_at_once")
    # ? To be filled from schedule
    start_datetime = models.DateTimeField(auto_now=False, auto_now_add=False, null=True, blank=True)
    end_datetime = models.DateTimeField(auto_now=False, auto_now_add=False, null=True, blank=True)
    waiting_duration = models.PositiveIntegerField(null=True, blank=True)
    extra_duration = models.PositiveIntegerField(null=True, blank=True)

    is_public = models.BooleanField(default=False)
    is_preparatory = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk:
            if not get_current_user().is_superuser:  # type: ignore
                self.organization_id = get_current_user_organization()
        return super().save(*args, **kwargs)

    class Meta:
        app_label = "exam_public"

    def set_exam_result(self):
        if self.total_obtainable_marks and self.obtained_marks and self.exam_status == "scored":
            passing_percentage = self.exam_backlog.passing_percentage
            passing_marks = (passing_percentage / 100) * self.total_obtainable_marks
            if self.obtained_marks >= passing_marks:
                self.exam_result = "pass"
            else:
                self.exam_result = "fail"
        else:
            self.exam_result = "pending"
        self.save()

    @classmethod
    def get_detail_queryset(
        cls,
        exam_backlog: bool = False,
        candidate: bool = False,
        q_filter: models.Q = models.Q(),
        exam_backlog_question: bool = False,
        get_answers: bool = False,
        exam_backlog_question_filter=models.Q(),
    ) -> models.QuerySet:
        return get_candidate_exam_detailed_queryset(
            cls, exam_backlog, candidate, q_filter, exam_backlog_question, get_answers, exam_backlog_question_filter
        )


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

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_candidateexam_retryhint"

    def save(self, *args, **kwargs):
        self.penalty_score = (self.exam_backlog_question.retry_penalty / 100) * self.exam_backlog_question.total_marks
        return super().save(*args, **kwargs)
