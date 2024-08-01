from django.db import models

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

    education_level = models.ForeignKey("questionbank.EducationLevel", on_delete=models.CASCADE)

    total_marks = models.PositiveIntegerField(default=0)
    pass_marks = models.PositiveIntegerField(default=0)

    is_global = models.BooleanField(default=True)

    class Meta:
        app_label = "exam_public"


# ---------------------------------------------------------------------------- #
#                               QUESTION BACKLOGS                              #
# ---------------------------------------------------------------------------- #
class ExamBacklogQuestion(BaseModel):
    exam_backlog = models.ForeignKey("exam_public.exambacklog", on_delete=models.CASCADE)
    subject = models.ForeignKey("questionbank.Subject", on_delete=models.DO_NOTHING)
    subject_name = models.CharField(max_length=255)
    # * Question Fields
    question = models.ForeignKey("questionbank.Question", on_delete=models.DO_NOTHING)
    type = models.ForeignKey("questionbank.QuestionType", on_delete=models.DO_NOTHING)
    title = models.CharField(max_length=255)
    text = models.TextField()
    max_retries = models.IntegerField(default=0)
    retry_penalty = models.IntegerField(default=0)
    sequence = models.PositiveIntegerField(default=1)

    can_shuffle = models.BooleanField(default=False)
    has_media = models.BooleanField(default=False)

    medias = models.ManyToManyField("lookups.Media", through="ExamBacklogQuestionMedia")

    difficulty = models.ForeignKey("questionbank.DifficultyLevel", on_delete=models.DO_NOTHING)
    difficulty_name = models.CharField(max_length=255)

    measuring_unit = models.ForeignKey("lookups.MeasuringUnit", on_delete=models.DO_NOTHING)
    measuring_unit_name = models.CharField(max_length=255)

    section = models.ForeignKey("exam_public.SectionBacklog", on_delete=models.DO_NOTHING, null=True)
    subsection = models.ForeignKey("exam_public.SubSectionBacklog", on_delete=models.DO_NOTHING, null=True)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question"


class ExamBacklogQuestionMedia(BaseModel):
    exam_question_backlog = models.ForeignKey(ExamBacklogQuestion, on_delete=models.CASCADE)

    media = models.ForeignKey("lookups.Media", on_delete=models.PROTECT)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_media"


# ------------------------------ CHOICE BACKLOGS ----------------------------- #


class ExamBacklogQuestionChoice(BaseModel):
    exam_question_backlog = models.ForeignKey(ExamBacklogQuestion, on_delete=models.CASCADE)
    # * Question Choice Fields
    question_choice = models.ForeignKey("questionbank.QuestionChoice", on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=255)
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
    exam_question_backlog_choice = models.ForeignKey(ExamBacklogQuestionChoice, on_delete=models.CASCADE)

    media = models.ForeignKey("lookups.Media", on_delete=models.PROTECT)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_choice_media"


# ------------------------------- TAG BACKLOGS ------------------------------- #


class ExamBacklogQuestionTag(BaseModel):
    exam_question_backlog = models.ForeignKey(ExamBacklogQuestion, on_delete=models.CASCADE)
    # * Question Tag Fields
    tag = models.ForeignKey("lookups.Tag", on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=255)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_tag"


# ---------------------------- RETRY HINT BACKLOGS --------------------------- #
class ExamBacklogQuestionRetryHint(BaseModel):
    exam_question_backlog = models.ForeignKey(ExamBacklogQuestion, on_delete=models.CASCADE)
    # * Question Retry Hint Fields
    retry_hint = models.ForeignKey("questionbank.QuestionRetryHint", on_delete=models.DO_NOTHING)
    text = models.TextField()
    has_media = models.BooleanField(default=False)
    sequence = models.IntegerField(default=1)

    medias = models.ManyToManyField("lookups.Media", through="ExamBacklogQuestionRetryHintMedia")

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_retryhint"


class ExamBacklogQuestionRetryHintMedia(BaseModel):
    exam_question_backlog_retry_hint = models.ForeignKey(ExamBacklogQuestionRetryHint, on_delete=models.CASCADE)

    media = models.ForeignKey("lookups.Media", on_delete=models.PROTECT)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_retryhint_media"


# ------------------------- ATTEMPT RESPONSE BACKLOG ------------------------- #


class ExamBacklogQuestionAttemptResponse(BaseModel):
    exam_question_backlog = models.ForeignKey(ExamBacklogQuestion, on_delete=models.CASCADE)
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


# ----------------------------- SECTION BACKLOGS ----------------------------- #


class SectionBacklog(BaseModel):
    exam = models.ForeignKey("exam_admin.Exam", on_delete=models.CASCADE)
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


class SubSectionBacklog(BaseModel):
    exam = models.ForeignKey("exam_admin.Exam", on_delete=models.CASCADE)
    # * SubSection Fields
    subsection = models.ForeignKey("exam_admin.SubSection", on_delete=models.DO_NOTHING)
    section = models.ForeignKey("exam_public.SectionBacklog", on_delete=models.DO_NOTHING)
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
