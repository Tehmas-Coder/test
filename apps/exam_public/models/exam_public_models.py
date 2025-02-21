from django.db import models

from apps.exam_public.helpers.queryset_functions import (
    get_candidate_detailed_queryset,
    get_candidate_exam_detailed_queryset,
)
from apps.user.utils.user_utils import get_current_user_organization
from core.models import BaseModel
from middlewares.current_user_middleware import get_current_user
from utils.datetime_utils import convert_any_datetime_to_utc, get_current_utc_datetime

MEDIA_MODEL = "user.Media"


class Candidate(BaseModel):
    """
    Represents a candidate in the system.

    - id: Autofield (PK)
    - user: BaseUser (FK)
    - organization: Organization (FK)
    - self_exam_creation_limit: PositiveIntegerField
    - self_exam_count: PositiveIntegerField
    - is_self_preparation_allowed: BooleanField
    """

    user = models.ForeignKey("user.BaseUser", on_delete=models.CASCADE, related_name="user_candidates")
    organization = models.ForeignKey("lookups.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="organization_candidates")

    self_exam_creation_limit = models.PositiveIntegerField(default=10)
    self_exam_count = models.PositiveIntegerField(default=0)

    is_self_preparation_allowed = models.BooleanField(default=False)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_candidate"

    @property
    def is_exam_limit_remaining(self):
        """
        Checks if the candidate can create more self-exams based on their current limit and returns a boolean value.
        """
        return self.self_exam_count < self.self_exam_creation_limit

    @classmethod
    def get_detail_queryset(cls, organization=False, user=False) -> models.QuerySet:
        return get_candidate_detailed_queryset(cls, organization, user)


class CandidateExam(BaseModel):
    """
    Represents an exam taken by a candidate.

    - id: Autofield (PK)
    - candidate: Candidate (FK)
    - exam_backlog: ExamBacklog (FK)
    - schedule: Schedule (FK)
    - organization: Organization (FK)
    - candidate_email: EmailField
    - total_obtainable_marks: FloatField
    - obtained_marks: FloatField
    - exam_duration: PositiveIntegerField
    - exam_status: CharField
        Choices:
            - "assigned"
            - "attempted"
            - "submitted"
            - "marked"
            - "scored"
            - "expired"
    - exam_result: CharField
        Choices:
            - "pass"
            - "fail"
            - "pending"
    - exam_questions_visibility: CharField
        Choices:
            - "all_at_once"
            - "one_by_one"
    - start_datetime: DateTimeField
    - end_datetime: DateTimeField
    - waiting_duration: PositiveIntegerField
    - extra_duration: PositiveIntegerField
    - is_public: BooleanField
    - is_preparatory: BooleanField
    - is_created_by_candidate: BooleanField
    """

    candidate = models.ForeignKey("exam_public.Candidate", on_delete=models.CASCADE, null=True, blank=True)
    exam_backlog = models.ForeignKey("exam_public.ExamBacklog", on_delete=models.CASCADE, related_name="candidate_exam_examsbacklog")
    schedule = models.ForeignKey("exam_admin.Schedule", on_delete=models.SET_NULL, null=True, blank=True)
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
    is_created_by_candidate = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """
        Sets the organization of the candidate exam if the user is not a superuser.
        """
        if not self.pk:
            if not get_current_user().is_superuser:  # type: ignore
                current_user_roles = get_current_user().get_user_role_slugs  # type: ignore
                if "candidate" not in current_user_roles:
                    self.organization_id = get_current_user_organization()
                else:
                    self.is_created_by_candidate = True
        return super().save(*args, **kwargs)

    class Meta:
        app_label = "exam_public"

    def set_exam_result(self):
        """
        Sets the exam result based on the obtained marks and passing percentage.
        """
        if self.exam_status == "scored" and self.exam_result == "pending":
            passing_percentage = self.exam_backlog.passing_percentage
            passing_marks = (passing_percentage / 100) * self.total_obtainable_marks
            if self.obtained_marks >= passing_marks:
                self.exam_result = "pass"
            else:
                self.exam_result = "fail"
        self.save()

    def is_expired(self):
        """
        Checks if the exam has expired and updates the exam status accordingly.
        """
        is_exam_expired = self.exam_status == "expired"
        if (not is_exam_expired) and self.end_datetime:
            is_exam_expired = convert_any_datetime_to_utc(self.end_datetime) < get_current_utc_datetime()
            if is_exam_expired:
                self.exam_status = "expired"
                self.save()
        return is_exam_expired

    @classmethod
    def get_detail_queryset(
        cls,
        exam_backlog: bool = False,
        candidate: bool = False,
        candidate_exam_id: int | None = None,
        q_filter: models.Q = models.Q(),
        exam_backlog_question: bool = False,
        get_answers: bool = False,
        exam_backlog_question_filter=models.Q(),
        is_organization_filter=False,
    ) -> models.QuerySet:
        """
        Returns a detailed queryset of candidate exams based on the provided filters.
        """
        return get_candidate_exam_detailed_queryset(
            cls,
            exam_backlog,
            candidate,
            q_filter,
            exam_backlog_question,
            get_answers,
            exam_backlog_question_filter,
            is_organization_filter,
            candidate_exam_id,
        )


class CandidateExamStatusLog(BaseModel):
    """
    Represents a log of status changes for a candidate's exam.

    - id: Autofield (PK)
    - candidate_exam: CandidateExam (FK)
    - exam_status: CharField
    """

    candidate_exam = models.ForeignKey("exam_public.CandidateExam", on_delete=models.CASCADE, related_name="status_logs")
    exam_status = models.CharField(max_length=100)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_candidateexam_statuslog"


class CandidateExamAnswer(BaseModel):
    """
    Represents an answer given by a candidate for an exam question.

    - id: Autofield (PK)
    - candidate_exam: CandidateExam (FK)
    - exam_backlog_question: ExamBacklogQuestion (FK)
    - exam_backlog_question_choice: ExamBacklogQuestionChoice (FK)
    - exam_backlog_question_choice_title: TextField
    - answer_text: TextField
    - score: FloatField
    - seconds_taken: IntegerField
    - is_attempted: BooleanField
    - is_correct: BooleanField
    - answer_files: Media (M2M)
    """

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
    """
    Represents a mapping between candidate exam answers and media files.

    - id: Autofield (PK)
    - candidate_exam_answer: CandidateExamAnswer (FK)
    - media: Media (FK)
    """

    candidate_exam_answer = models.ForeignKey(CandidateExamAnswer, on_delete=models.CASCADE)
    media = models.ForeignKey(MEDIA_MODEL, on_delete=models.CASCADE)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_candidateexam_answer_media"


class CandidateExamRetryhint(BaseModel):
    """
    Represents a retry hint for a candidate's exam question.

    - id: Autofield (PK)
    - candidate_exam: CandidateExam (FK)
    - exam_backlog_question_retry_hint: ExamBacklogQuestionRetryHint (FK)
    - exam_backlog_question: ExamBacklogQuestion (FK)
    - penalty_score: DecimalField
    """

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
        """
        - Calculates the penalty score for the retry hint and saves the instance.
        - The penalty score is calculated as the percentage of the total marks of the exam question multiplied by the retry penalty.
        """
        self.penalty_score = (self.exam_backlog_question.retry_penalty / 100) * self.exam_backlog_question.total_marks
        return super().save(*args, **kwargs)
