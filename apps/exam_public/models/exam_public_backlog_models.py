from django.db import models

from apps.exam_public.helpers.queryset_functions import (
    get_exambacklogquestion_detailed_queryset,
)
from core.models import BaseModel

# ---------------------------------------------------------------------------- #
#                                 EXAM BACKLOG                                 #
# ---------------------------------------------------------------------------- #


class ExamBacklog(BaseModel):
    """
    Represents an exam backlog.

    - id: Autofield (PK)
    - exam: Exam (FK)
    - education_level: EducationLevel (FK)
    - name: CharField
    - code: CharField
    - abbreviation: CharField
    - instructions: TextField
    - education_level_name: CharField
    - total_marks: PositiveIntegerField
    - passing_percentage: PositiveIntegerField
    - is_global: BooleanField
    - examiners: BaseUser (M2M)
    """

    exam = models.ForeignKey("exam_admin.Exam", on_delete=models.DO_NOTHING)
    education_level = models.ForeignKey("questionbank.EducationLevel", on_delete=models.DO_NOTHING)

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10, blank=True)
    abbreviation = models.CharField(max_length=10, blank=True)
    instructions = models.TextField(null=True, blank=True)
    education_level_name = models.CharField(max_length=255)
    total_marks = models.PositiveIntegerField(default=0)
    passing_percentage = models.PositiveIntegerField(default=0)

    is_global = models.BooleanField(default=True)

    examiners = models.ManyToManyField("user.BaseUser", through="ExamBacklogExaminer", through_fields=("exam_backlog", "examiner"))

    class Meta:
        app_label = "exam_public"


# --------------------------- EXAM BACKLOG EXAMINER -------------------------- #
class ExamBacklogExaminer(BaseModel):
    """
    Represents an examiner for an exam backlog.

    - id: Autofield (PK)
    - exam_backlog: ExamBacklog (FK)
    - examiner: BaseUser (FK)
    """

    exam_backlog = models.ForeignKey("exam_public.ExamBacklog", on_delete=models.CASCADE)
    examiner = models.ForeignKey("user.BaseUser", on_delete=models.CASCADE)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_examiner"


# ---------------------------------------------------------------------------- #
#                               QUESTION BACKLOGS                              #
# ---------------------------------------------------------------------------- #
class ExamBacklogQuestion(BaseModel):
    """
    Represents a question in an exam backlog.

    - id: Autofield (PK)
    - exam_backlog: ExamBacklog (FK)
    - subject: Subject (FK)
    - difficulty_level: DifficultyLevel (FK)
    - measuring_unit: MeasuringUnit (FK)
    - section_backlog: SectionBacklog (FK)
    - subsection_backlog: SubSectionBacklog (FK)
    - education_level: EducationLevel (FK)
    - subject_name: CharField
    - education_level_name: CharField
    - question: Question (FK)
    - type: QuestionType (FK)
    - title: TextField
    - text: TextField
    - max_retries: IntegerField
    - retry_penalty: IntegerField
    - sequence: PositiveIntegerField
    - time_limit: IntegerField
    - total_marks: IntegerField
    - can_shuffle: BooleanField
    - is_optional: BooleanField
    - is_public: BooleanField
    - is_global: BooleanField
    - has_media: BooleanField
    - medias: Media (M2M)
    - countries: Country (M2M)
    """

    exam_backlog = models.ForeignKey("exam_public.exambacklog", on_delete=models.CASCADE, related_name="backlog_questions")
    subject = models.ForeignKey("questionbank.Subject", on_delete=models.DO_NOTHING)
    difficulty_level = models.ForeignKey("questionbank.DifficultyLevel", on_delete=models.DO_NOTHING)
    measuring_unit = models.ForeignKey("lookups.MeasuringUnit", on_delete=models.DO_NOTHING)
    section_backlog = models.ForeignKey("exam_public.SectionBacklog", on_delete=models.DO_NOTHING, null=True)
    subsection_backlog = models.ForeignKey("exam_public.SubSectionBacklog", on_delete=models.DO_NOTHING, null=True)
    education_level = models.ForeignKey("questionbank.EducationLevel", on_delete=models.DO_NOTHING)

    subject_name = models.CharField(max_length=255)
    education_level_name = models.CharField(max_length=255)

    # * Question Fields
    question = models.ForeignKey("questionbank.Question", on_delete=models.DO_NOTHING)
    type = models.ForeignKey("questionbank.QuestionType", on_delete=models.DO_NOTHING)

    title = models.TextField()
    text = models.TextField(null=True, blank=True)
    max_retries = models.IntegerField(default=0)
    retry_penalty = models.IntegerField(default=0)
    sequence = models.PositiveIntegerField(default=1)
    time_limit = models.IntegerField(default=0)
    total_marks = models.IntegerField(default=0)

    can_shuffle = models.BooleanField(default=False)
    is_optional = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    is_global = models.BooleanField(default=False)
    has_media = models.BooleanField(default=False)

    medias = models.ManyToManyField("user.Media", through="ExamBacklogQuestionMedia")
    countries = models.ManyToManyField("lookups.Country", through="ExamBacklogQuestionCountry")

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question"

    @classmethod
    def get_detail_queryset(cls, all=False, get_answers=False, q_filter=models.Q(), candidate_exam_id: int | None = None):
        """
        Returns a queryset of ExamBacklogQuestion objects with prefetches.
        """
        return get_exambacklogquestion_detailed_queryset(cls, all, get_answers, q_filter, candidate_exam_id)


# -------------------------- QUESTION MEDIA BACKLOG -------------------------- #
class ExamBacklogQuestionMedia(BaseModel):
    """
    Represents media associated with a question in an exam backlog.

    - id: Autofield (PK)
    - exam_backlog_question: ExamBacklogQuestion (FK)
    - media: Media (FK)
    """

    exam_backlog_question = models.ForeignKey(ExamBacklogQuestion, on_delete=models.CASCADE)
    media = models.ForeignKey("user.Media", on_delete=models.PROTECT)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_media"


# ------------------------- QUESTION COUNTRY BACKLOG ------------------------- #


class ExamBacklogQuestionCountry(BaseModel):
    """
    Represents a country associated with a question in an exam backlog.

    - id: Autofield (PK)
    - exam_backlog_question: ExamBacklogQuestion (FK)
    - country: Country (FK)
    """

    exam_backlog_question = models.ForeignKey(ExamBacklogQuestion, on_delete=models.CASCADE)
    country = models.ForeignKey("lookups.Country", on_delete=models.CASCADE)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_country"


# ------------------------------ CHOICE BACKLOGS ----------------------------- #
class ExamBacklogQuestionChoice(BaseModel):
    """
    Represents a choice for a question in an exam backlog.

    - id: Autofield (PK)
    - exam_backlog_question: ExamBacklogQuestion (FK)
    - question_choice: QuestionChoice (FK)
    - title: CharField
    - text: TextField
    - weight: IntegerField
    - is_negative_weight: BooleanField
    - is_correct: BooleanField
    - has_media: BooleanField
    - medias: Media (M2M)
    """

    exam_backlog_question = models.ForeignKey(ExamBacklogQuestion, on_delete=models.CASCADE, related_name="backlog_choices")

    # * Question Choice Fields
    question_choice = models.ForeignKey("questionbank.QuestionChoice", on_delete=models.DO_NOTHING)

    title = models.CharField(max_length=255)
    text = models.TextField(null=True, blank=True)
    weight = models.IntegerField(default=0)

    is_negative_weight = models.BooleanField(default=False)
    is_correct = models.BooleanField(default=False)
    has_media = models.BooleanField(default=False)

    medias = models.ManyToManyField("user.Media", through="ExamBacklogQuestionChoiceMedia")

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_choice"


class ExamBacklogQuestionChoiceMedia(BaseModel):
    """
    Represents media associated with a choice in an exam backlog.

    - id: Autofield (PK)
    - exam_backlog_question_choice: ExamBacklogQuestionChoice (FK)
    - media: Media (FK)
    """

    exam_backlog_question_choice = models.ForeignKey(ExamBacklogQuestionChoice, on_delete=models.CASCADE)
    media = models.ForeignKey("user.Media", on_delete=models.PROTECT)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_choice_media"


# ------------------------------- TAG BACKLOGS ------------------------------- #
class ExamBacklogQuestionTag(BaseModel):
    """
    Represents a tag associated with a question in an exam backlog.

    - id: Autofield (PK)
    - exam_backlog_question: ExamBacklogQuestion (FK)
    - tag: Tag (FK)
    - name: CharField
    """

    exam_backlog_question = models.ForeignKey(ExamBacklogQuestion, on_delete=models.CASCADE, related_name="backlog_tags")

    # * Question Tag Fields
    tag = models.ForeignKey("questionbank.Tag", on_delete=models.DO_NOTHING)

    name = models.CharField(max_length=255)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_tag"


# ---------------------------- RETRY HINT BACKLOGS --------------------------- #
class ExamBacklogQuestionRetryHint(BaseModel):
    """
    Represents a retry hint for a question in an exam backlog.

    - id: Autofield (PK)
    - exam_backlog_question: ExamBacklogQuestion (FK)
    - retry_hint: QuestionRetryHint (FK)
    - text: TextField
    - sequence: IntegerField
    - has_media: BooleanField
    - medias: Media (M2M)
    """

    exam_backlog_question = models.ForeignKey(ExamBacklogQuestion, on_delete=models.CASCADE, related_name="backlog_retry_hints")

    # * Question Retry Hint Fields
    retry_hint = models.ForeignKey("questionbank.QuestionRetryHint", on_delete=models.DO_NOTHING)

    text = models.TextField(null=True, blank=True)
    sequence = models.IntegerField(default=1)
    has_media = models.BooleanField(default=False)

    medias = models.ManyToManyField("user.Media", through="ExamBacklogQuestionRetryHintMedia")

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_retryhint"

    @classmethod
    def get_detail_queryset(cls, media=True, q_filter=models.Q()):
        """
        Returns a queryset of ExamBacklogQuestionRetryHint objects with prefetches.
        """
        return cls.objects.filter(q_filter).prefetch_related(
            models.Prefetch("exambacklogquestionretryhintmedia_set", queryset=ExamBacklogQuestionRetryHintMedia.objects.all().select_related("media"))
        )


class ExamBacklogQuestionRetryHintMedia(BaseModel):
    """
    Represents media associated with a retry hint in an exam backlog.

    - id: Autofield (PK)
    - exam_backlog_question_retry_hint: ExamBacklogQuestionRetryHint (FK)
    - media: Media (FK)
    """

    exam_backlog_question_retry_hint = models.ForeignKey(ExamBacklogQuestionRetryHint, on_delete=models.CASCADE)
    media = models.ForeignKey("user.Media", on_delete=models.PROTECT)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_exambacklog_question_retryhint_media"


# ------------------------- ATTEMPT RESPONSE BACKLOG ------------------------- #
class ExamBacklogQuestionAttemptResponse(BaseModel):
    """
    Represents an attempt response for a question in an exam backlog.

    - id: Autofield (PK)
    - exam_backlog_question: ExamBacklogQuestion (FK)
    - attempt_response: QuestionAttemptResponse (FK)
    - text: TextField
    - type: CharField
    """

    exam_backlog_question = models.ForeignKey(ExamBacklogQuestion, on_delete=models.CASCADE, related_name="backlog_attempt_responses")

    # * Question Attempt Response Fields
    attempt_response = models.ForeignKey("questionbank.QuestionAttemptResponse", on_delete=models.DO_NOTHING)

    text = models.TextField(null=True, blank=True)
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
    """
    Represents a section in an exam backlog.

    - id: Autofield (PK)
    - exam_backlog: ExamBacklog (FK)
    - section: Section (FK)
    - measuring_unit: MeasuringUnit (FK)
    - title: CharField
    - sequence: PositiveIntegerField
    - time_limit: PositiveIntegerField
    - is_global: BooleanField
    - is_shuffle: BooleanField
    """

    exam_backlog = models.ForeignKey("exam_public.exambacklog", on_delete=models.CASCADE, related_name="section_backlogs")

    # * Section Fields
    section = models.ForeignKey("exam_admin.Section", on_delete=models.DO_NOTHING)
    measuring_unit = models.ForeignKey("lookups.MeasuringUnit", on_delete=models.DO_NOTHING)

    title = models.CharField(max_length=255)
    sequence = models.PositiveIntegerField(default=1)
    time_limit = models.PositiveIntegerField(null=True)

    is_global = models.BooleanField(default=True)
    is_shuffle = models.BooleanField(default=False)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_sectionbacklog"


# ---------------------------- SUBSECTION BACKLOG --------------------------- #
class SubSectionBacklog(BaseModel):
    """
    Represents a subsection in an exam backlog.

    - id: Autofield (PK)
    - exam_backlog: ExamBacklog (FK)
    - subsection: SubSection (FK)
    - section: SectionBacklog (FK)
    - measuring_unit: MeasuringUnit (FK)
    - title: CharField
    - sequence: PositiveIntegerField
    - time_limit: PositiveIntegerField
    - is_global: BooleanField
    - is_shuffle: BooleanField
    """

    exam_backlog = models.ForeignKey("exam_public.exambacklog", on_delete=models.CASCADE)

    # * SubSection Fields
    subsection = models.ForeignKey("exam_admin.SubSection", on_delete=models.DO_NOTHING)
    section = models.ForeignKey("exam_public.SectionBacklog", on_delete=models.DO_NOTHING, related_name="subsection_backlogs")
    measuring_unit = models.ForeignKey("lookups.MeasuringUnit", on_delete=models.DO_NOTHING)

    title = models.CharField(max_length=255)
    sequence = models.PositiveIntegerField(default=1)
    time_limit = models.PositiveIntegerField(null=True)

    is_global = models.BooleanField(default=True)
    is_shuffle = models.BooleanField(default=False)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_subsectionbacklog"
