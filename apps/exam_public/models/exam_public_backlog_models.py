from django.db import models
from django.db.models import Prefetch, Q, QuerySet

from core.models import BaseModel

# ---------------------------------------------------------------------------- #
#                                 EXAM BACKLOG                                 #
# ---------------------------------------------------------------------------- #


class ExamBacklog(BaseModel):
    exam = models.ForeignKey("exam_admin.Exam", on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10, blank=True)
    abbreviation = models.CharField(max_length=10, blank=True)
    instructions = models.TextField()

    education_level = models.ForeignKey("questionbank.EducationLevel", on_delete=models.DO_NOTHING)
    education_level_name = models.CharField(max_length=255)

    total_marks = models.PositiveIntegerField(default=0)
    pass_marks = models.PositiveIntegerField(default=0)

    is_global = models.BooleanField(default=True)

    class Meta:
        app_label = "exam_public"


# ---------------------------------------------------------------------------- #
#                               QUESTION BACKLOGS                              #
# ---------------------------------------------------------------------------- #
class ExamBacklogQuestion(BaseModel):
    exam_backlog = models.ForeignKey("exam_public.exambacklog", on_delete=models.CASCADE, related_name="backlog_questions")
    subject = models.ForeignKey("questionbank.Subject", on_delete=models.DO_NOTHING)
    subject_name = models.CharField(max_length=255)
    education_level = models.ForeignKey("questionbank.EducationLevel", on_delete=models.DO_NOTHING)
    education_level_name = models.CharField(max_length=255)
    # * Question Fields
    question = models.ForeignKey("questionbank.Question", on_delete=models.DO_NOTHING)
    type = models.ForeignKey("questionbank.QuestionType", on_delete=models.DO_NOTHING)
    title = models.CharField(max_length=255)
    text = models.TextField()
    max_retries = models.IntegerField(default=0)
    retry_penalty = models.IntegerField(default=0)
    sequence = models.PositiveIntegerField(default=1)
    time_limit = models.IntegerField(default=0)
    total_marks = models.IntegerField(default=0)

    can_shuffle = models.BooleanField(default=False)
    is_optional = models.BooleanField(default=False)
    is_global = models.BooleanField(default=False)
    has_media = models.BooleanField(default=False)

    difficulty = models.ForeignKey("questionbank.DifficultyLevel", on_delete=models.DO_NOTHING)
    difficulty_name = models.CharField(max_length=255)

    measuring_unit = models.ForeignKey("lookups.MeasuringUnit", on_delete=models.DO_NOTHING)
    measuring_unit_name = models.CharField(max_length=255)

    section_backlog = models.ForeignKey("exam_public.SectionBacklog", on_delete=models.DO_NOTHING, null=True)
    subsection_backlog = models.ForeignKey("exam_public.SubSectionBacklog", on_delete=models.DO_NOTHING, null=True)

    medias = models.ManyToManyField("lookups.Media", through="ExamBacklogQuestionMedia")
    countries = models.ManyToManyField("lookups.Country", through="ExamBacklogQuestionCountry")

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question"


# -------------------------- QUESTION MEDIA BACKLOG -------------------------- #


class ExamBacklogQuestionMedia(BaseModel):
    exam_backlog_question = models.ForeignKey(ExamBacklogQuestion, on_delete=models.CASCADE)
    media = models.ForeignKey("lookups.Media", on_delete=models.PROTECT)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_media"


# ------------------------- QUESTION COUNTRY BACKLOG ------------------------- #


class ExamBacklogQuestionCountry(BaseModel):
    exam_backlog_question = models.ForeignKey(ExamBacklogQuestion, on_delete=models.CASCADE)
    country = models.ForeignKey("lookups.Country", on_delete=models.CASCADE)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_country"


# ------------------------------ CHOICE BACKLOGS ----------------------------- #


class ExamBacklogQuestionChoice(BaseModel):
    exam_backlog_question = models.ForeignKey(ExamBacklogQuestion, on_delete=models.CASCADE, related_name="backlog_choices")
    # * Question Choice Fields
    question_choice = models.ForeignKey("questionbank.QuestionChoice", on_delete=models.DO_NOTHING)
    title = models.CharField(max_length=255)
    text = models.TextField()
    weight = models.IntegerField(default=0)

    is_negative_weight = models.BooleanField(default=False)
    is_correct = models.BooleanField(default=False)
    has_media = models.BooleanField(default=False)

    medias = models.ManyToManyField("lookups.Media", through="ExamBacklogQuestionChoiceMedia")

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_choice"


class ExamBacklogQuestionChoiceMedia(BaseModel):
    exam_backlog_question_choice = models.ForeignKey(ExamBacklogQuestionChoice, on_delete=models.CASCADE)
    media = models.ForeignKey("lookups.Media", on_delete=models.PROTECT)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_choice_media"


# ------------------------------- TAG BACKLOGS ------------------------------- #


class ExamBacklogQuestionTag(BaseModel):
    exam_backlog_question = models.ForeignKey(ExamBacklogQuestion, on_delete=models.CASCADE, related_name="backlog_tags")
    # * Question Tag Fields
    tag = models.ForeignKey("lookups.Tag", on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=255)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_tag"


# ---------------------------- RETRY HINT BACKLOGS --------------------------- #


class ExamBacklogQuestionRetryHint(BaseModel):
    exam_backlog_question = models.ForeignKey(ExamBacklogQuestion, on_delete=models.CASCADE, related_name="backlog_retry_hints")
    # * Question Retry Hint Fields
    retry_hint = models.ForeignKey("questionbank.QuestionRetryHint", on_delete=models.DO_NOTHING)
    text = models.TextField()
    sequence = models.IntegerField(default=1)

    has_media = models.BooleanField(default=False)

    medias = models.ManyToManyField("lookups.Media", through="ExamBacklogQuestionRetryHintMedia")

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_retryhint"


class ExamBacklogQuestionRetryHintMedia(BaseModel):
    exam_backlog_question_retry_hint = models.ForeignKey(ExamBacklogQuestionRetryHint, on_delete=models.CASCADE)
    media = models.ForeignKey("lookups.Media", on_delete=models.PROTECT)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_retryhint_media"


# ------------------------- ATTEMPT RESPONSE BACKLOG ------------------------- #


class ExamBacklogQuestionAttemptResponse(BaseModel):
    exam_backlog_question = models.ForeignKey(ExamBacklogQuestion, on_delete=models.CASCADE, related_name="backlog_attempt_responses")
    # * Question Attempt Response Fields
    attempt_response = models.ForeignKey("questionbank.QuestionAttemptResponse", on_delete=models.DO_NOTHING)
    text = models.TextField()
    TYPE_CHOICES = (
        ("correct", "Correct"),
        ("wrong", "Wrong"),
        ("partial", "Partial"),
        ("skipped", "Skipped"),
        ("unanswered", "Unanswered"),
    )

    type = models.CharField(max_length=100, choices=TYPE_CHOICES, default="unanswered")

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_attemptresponse"


# ----------------------------- SECTION BACKLOG ----------------------------- #


class SectionBacklog(BaseModel):
    exam_backlog = models.ForeignKey("exam_public.exambacklog", on_delete=models.CASCADE, related_name="section_backlogs")
    # * Section Fields
    section = models.ForeignKey("exam_admin.Section", on_delete=models.DO_NOTHING)
    measuring_unit = models.ForeignKey("lookups.MeasuringUnit", on_delete=models.DO_NOTHING)

    title = models.CharField(max_length=255)
    sequence = models.PositiveIntegerField(default=1)

    time_limit = models.PositiveIntegerField(null=True)
    total_marks = models.PositiveIntegerField(default=0)
    passing_marks = models.PositiveIntegerField(null=True)

    is_global = models.BooleanField(default=True)
    is_shuffle = models.BooleanField(default=False)
    is_negative_marking = models.BooleanField(default=False)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_sectionbacklog"


# ---------------------------- SUBSECTION BACKLOG --------------------------- #


class SubSectionBacklog(BaseModel):
    exam_backlog = models.ForeignKey("exam_public.exambacklog", on_delete=models.CASCADE)
    # * SubSection Fields
    subsection = models.ForeignKey("exam_admin.SubSection", on_delete=models.DO_NOTHING)
    section = models.ForeignKey("exam_public.SectionBacklog", on_delete=models.DO_NOTHING, related_name="subsection_backlogs")
    measuring_unit = models.ForeignKey("lookups.MeasuringUnit", on_delete=models.DO_NOTHING)

    title = models.CharField(max_length=255)
    sequence = models.PositiveIntegerField(default=1)

    time_limit = models.PositiveIntegerField(null=True)
    total_marks = models.PositiveIntegerField(default=0)
    passing_marks = models.PositiveIntegerField(null=True)

    is_global = models.BooleanField(default=True)
    is_shuffle = models.BooleanField(default=False)
    is_negative_marking = models.BooleanField(default=False)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_subsectionbacklog"
