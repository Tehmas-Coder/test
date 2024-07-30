from django.db import models

from core.models import BaseModel


# ---------------------------------------------------------------------------- #
#                               QUESTION BACKLOGS                              #
# ---------------------------------------------------------------------------- #
class UserExamQuestionBacklog(BaseModel):
    user_exam = models.ForeignKey("exam_admin.UserExam", on_delete=models.CASCADE)
    subject = models.ForeignKey("questionbank.Subject", on_delete=models.CASCADE)
    subject_name = models.CharField(max_length=255)
    # * Question Fields
    question = models.ForeignKey("questionbank.Question", on_delete=models.CASCADE)
    type = models.ForeignKey("questionbank.QuestionType", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    text = models.TextField()
    max_retries = models.IntegerField(default=0)
    retry_penalty = models.IntegerField(default=0)

    can_shuffle = models.BooleanField(default=False)
    has_media = models.BooleanField(default=False)
    sequence = models.PositiveIntegerField(default=1)

    medias = models.ManyToManyField("lookups.Media", through="UserExamQuestionBacklogMedia")

    difficulty = models.ForeignKey("questionbank.DifficultyLevel", on_delete=models.CASCADE)
    difficulty_name = models.CharField(max_length=255)

    measuring_unit = models.ForeignKey("lookups.MeasuringUnit", on_delete=models.CASCADE)
    measuring_unit_name = models.CharField(max_length=255)

    section = models.ForeignKey("exam_admin.SectionBacklog", on_delete=models.CASCADE, null=True)
    subsection = models.ForeignKey("exam_admin.SubSectionBacklog", on_delete=models.CASCADE, null=True)

    class Meta:
        app_label = "exam_admin"
        db_table = "exam_admin_userexam_questionbacklog"


class UserExamQuestionBacklogMedia(BaseModel):
    user_exam_question_backlog = models.ForeignKey(UserExamQuestionBacklog, on_delete=models.CASCADE)

    media = models.ForeignKey("lookups.Media", on_delete=models.CASCADE)

    class Meta:
        app_label = "exam_admin"
        db_table = "exam_admin_userexam_questionbacklog_media"


# ------------------------------ CHOICE BACKLOGS ----------------------------- #


class UserExamQuestionBacklogChoice(BaseModel):
    user_exam_question_backlog = models.ForeignKey(UserExamQuestionBacklog, on_delete=models.CASCADE)
    # * Question Choice Fields
    question_choice = models.ForeignKey("questionbank.QuestionChoice", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    text = models.TextField()
    weight = models.IntegerField(default=0)

    is_negative_weight = models.BooleanField(default=False)
    is_correct = models.BooleanField(default=False)

    has_media = models.BooleanField(default=False)

    medias = models.ManyToManyField("lookups.Media", through="UserExamQuestionBacklogChoiceMedia")

    class Meta:
        app_label = "exam_admin"
        db_table = "exam_admin_userexam_questionbacklog_choice"


class UserExamQuestionBacklogChoiceMedia(BaseModel):
    user_exam_question_backlog_choice = models.ForeignKey(UserExamQuestionBacklogChoice, on_delete=models.CASCADE)

    media = models.ForeignKey("lookups.Media", on_delete=models.CASCADE)

    class Meta:
        app_label = "exam_admin"
        db_table = "exam_admin_userexam_questionbacklog_choice_media"


# ------------------------------- TAG BACKLOGS ------------------------------- #


class UserExamQuestionBacklogTag(BaseModel):
    user_exam_question_backlog = models.ForeignKey(UserExamQuestionBacklog, on_delete=models.CASCADE)
    # * Question Tag Fields
    tag = models.ForeignKey("lookups.Tag", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    class Meta:
        app_label = "exam_admin"
        db_table = "exam_admin_userexam_questionbacklog_tag"


# ---------------------------- RETRY HINT BACKLOGS --------------------------- #
class UserExamQuestionBacklogRetryHint(BaseModel):
    user_exam_question_backlog = models.ForeignKey(UserExamQuestionBacklog, on_delete=models.CASCADE)
    # * Question Retry Hint Fields
    retry_hint = models.ForeignKey("questionbank.QuestionRetryHint", on_delete=models.CASCADE)
    text = models.TextField()
    has_media = models.BooleanField(default=False)
    sequence = models.IntegerField(default=1)

    medias = models.ManyToManyField("lookups.Media", through="UserExamQuestionBacklogRetryHintMedia")

    class Meta:
        app_label = "exam_admin"
        db_table = "exam_admin_userexam_questionbacklog_retryhint"


class UserExamQuestionBacklogRetryHintMedia(BaseModel):
    user_exam_question_backlog_retry_hint = models.ForeignKey(UserExamQuestionBacklogRetryHint, on_delete=models.CASCADE)

    media = models.ForeignKey("lookups.Media", on_delete=models.CASCADE)

    class Meta:
        app_label = "exam_admin"
        db_table = "exam_admin_userexam_questionbacklog_retryhint_media"


# ------------------------- ATTEMPT RESPONSE BACKLOG ------------------------- #


class UserExamQuestionBacklogAttemptResponse(BaseModel):
    user_exam_question_backlog = models.ForeignKey(UserExamQuestionBacklog, on_delete=models.CASCADE)
    # * Question Attempt Response Fields
    attempt_response = models.ForeignKey("questionbank.QuestionAttemptResponse", on_delete=models.CASCADE)
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
        app_label = "exam_admin"
        db_table = "exam_admin_userexam_questionbacklog_attemptresponse"


# ----------------------------- SECTION BACKLOGS ----------------------------- #


class SectionBacklog(BaseModel):
    user_exam = models.ForeignKey("exam_admin.UserExam", on_delete=models.CASCADE)
    subsections = models.ManyToManyField("exam_admin.SubSectionBacklog", through="SectionBacklogSubSection")
    # * Section Fields
    section = models.ForeignKey("exam_admin.Section", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    sequence = models.PositiveIntegerField(default=1)

    time_limit = models.PositiveIntegerField(null=True)
    total_marks = models.PositiveIntegerField(default=0)
    passing_marks = models.PositiveIntegerField(null=True)

    is_global = models.BooleanField(default=True)
    is_shuffle = models.BooleanField(default=False)
    is_negative_marking = models.BooleanField(default=False)

    class Meta:
        app_label = "exam_admin"
        db_table = "exam_admin_sectionbacklog"


class SubSectionBacklog(BaseModel):
    user_exam = models.ForeignKey("exam_admin.UserExam", on_delete=models.CASCADE)
    # * SubSection Fields
    subsection = models.ForeignKey("exam_admin.SubSection", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    sequence = models.PositiveIntegerField(default=1)

    time_limit = models.PositiveIntegerField(null=True)
    total_marks = models.PositiveIntegerField(default=0)
    passing_marks = models.PositiveIntegerField(null=True)

    is_global = models.BooleanField(default=True)
    is_shuffle = models.BooleanField(default=False)
    is_negative_marking = models.BooleanField(default=False)

    class Meta:
        app_label = "exam_admin"
        db_table = "exam_admin_subsectionbacklog"


class SectionBacklogSubSection(BaseModel):
    section_backlog = models.ForeignKey(SectionBacklog, on_delete=models.CASCADE)
    subsection_backlog = models.ForeignKey(SubSectionBacklog, on_delete=models.CASCADE)

    class Meta:
        app_label = "exam_admin"
        db_table = "exam_admin_sectionbacklog_subsectionbacklog"
