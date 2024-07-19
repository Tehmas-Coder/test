from django.db import models
from core.models import BaseModel
from datetime import datetime

# ---------------------------------------------------------------------------- #
#                               QUESTION LOOKUPS                               #
# ---------------------------------------------------------------------------- #


def upload_to(instance, filename):
    folder_name = instance.__class__.__name__.lower()
    timestamp = int(datetime.now().timestamp())
    return f"{folder_name}/{timestamp}_{filename}"


class Media(BaseModel):
    name = models.CharField(max_length=100)
    file = models.FileField(upload_to=upload_to)
    type = models.ForeignKey("lookups.MediaType", on_delete=models.CASCADE)
    extension = models.CharField(max_length=10, blank=True)
    size = models.IntegerField(default=0)

    class Meta:
        app_label = "questionbank"


class EducationLevel(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    abbreviation = models.CharField(max_length=10, blank=True)

    def save(self, *args, **kwargs):
        self.slug = self.name.lower().replace(" ", "-")
        super().save(*args, **kwargs)

    class Meta:
        app_label = "questionbank"


class Subject(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    abbreviation = models.CharField(max_length=10, blank=True)

    education_levels = models.ManyToManyField(
        EducationLevel, through="SubjectEducationLevel", related_name="subjects"
    )

    @property
    def full_name(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        self.slug = self.name.lower().replace(" ", "-")
        super().save(*args, **kwargs)

    class Meta:
        app_label = "questionbank"


class QuestionType(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    abbreviation = models.CharField(max_length=10, blank=True)

    def save(self, *args, **kwargs):
        self.slug = self.name.lower().replace(" ", "-")
        super().save(*args, **kwargs)

    class Meta:
        app_label = "questionbank"


class DifficultyLevel(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    abbreviation = models.CharField(max_length=10, blank=True)
    sequence = models.IntegerField(default=1)

    def save(self, *args, **kwargs):
        self.slug = self.name.lower().replace(" ", "-")
        super().save(*args, **kwargs)

    class Meta:
        app_label = "questionbank"


# ---------------------------------------------------------------------------- #
#                                   QUESTION                                   #
# ---------------------------------------------------------------------------- #


class Question(BaseModel):
    title = models.CharField(max_length=255)
    text = models.TextField()

    subject_education_levels = models.ManyToManyField(
        "SubjectEducationLevel",
        through="QuestionSubject",
        related_name="questions",
    )

    tags = models.ManyToManyField(
        "lookups.Tag", related_name="questions", through="QuestionTag"
    )

    max_retries = models.IntegerField(default=0)
    retry_penalty = models.IntegerField(default=0)

    can_shuffle = models.BooleanField(default=False)
    has_media = models.BooleanField(default=False)

    medias = models.ManyToManyField(
        Media, related_name="questions", through="QuestionMedia"
    )

    class Meta:
        app_label = "questionbank"

    @classmethod
    def get_questions_for_countries(cls, country_ids: list):
        from apps.questionbank.utils.question_utils import get_question_detail_queryset

        return (
            get_question_detail_queryset()
            .filter(subjects__subject_countries__country_id__in=country_ids)
            .distinct()
        )

    @classmethod
    def get_questions_for_subjects(cls, subject_ids: list):
        from apps.questionbank.utils.question_utils import get_question_detail_queryset

        return (
            get_question_detail_queryset()
            .filter(subjects__subject_education_level__subject_id__in=subject_ids)
            .distinct()
        )


class QuestionChoice(BaseModel):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    title = models.CharField(max_length=255)
    text = models.TextField()
    weight = models.IntegerField(default=0)

    is_negative_weight = models.BooleanField(default=False)
    is_correct = models.BooleanField(default=False)

    has_media = models.BooleanField(default=False)

    medias = models.ManyToManyField(Media, related_name="choices")

    class Meta:
        app_label = "questionbank"


class QuestionAttemptResponse(BaseModel):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="attempt_responses"
    )
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
        app_label = "questionbank"


class QuestionRetryHint(BaseModel):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="retry_hints"
    )
    text = models.TextField()
    has_media = models.BooleanField(default=False)
    sequence = models.IntegerField(default=1)

    medias = models.ManyToManyField(Media, related_name="retry_hints")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # self.arrange_sequence()

    def arrange_sequence(self):
        question_retry_hints = QuestionRetryHint.objects.filter(
            question=self.question
        ).order_by("sequence")
        for index, question_retry_hint in enumerate(question_retry_hints):
            question_retry_hint.sequence = index + 1
            question_retry_hint.save()

    class Meta:
        app_label = "questionbank"


# ---------------------------------------------------------------------------- #
#                                   MAPPINGS                                   #
# ---------------------------------------------------------------------------- #


class QuestionMedia(BaseModel):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
    )
    media = models.ForeignKey(Media, on_delete=models.CASCADE)

    class Meta:
        app_label = "questionbank"
        db_table = "questionbank_question_medias"


class QuestionTag(BaseModel):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
    )
    tag = models.ForeignKey("lookups.Tag", on_delete=models.CASCADE)

    class Meta:
        app_label = "questionbank"
        db_table = "questionbank_question_tags"


class SubjectEducationLevel(BaseModel):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
    )
    education_level = models.ForeignKey(EducationLevel, on_delete=models.CASCADE)

    class Meta:
        app_label = "questionbank"


class QuestionSubject(BaseModel):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="subjects"
    )
    subject_education_level = models.ForeignKey(
        SubjectEducationLevel,
        on_delete=models.CASCADE,
        related_name="question_subjects",
    )
    difficulty_level = models.ForeignKey(DifficultyLevel, on_delete=models.CASCADE)
    measuring_unit = models.ForeignKey(
        "lookups.MeasuringUnit", on_delete=models.CASCADE
    )
    countries = models.ManyToManyField(
        "lookups.Country", through="QuestionSubjectCountry"
    )

    time_limit = models.IntegerField(default=0)
    total_marks = models.IntegerField(default=0)
    is_optional = models.BooleanField(default=False)
    is_global = models.BooleanField(default=False)

    class Meta:
        app_label = "questionbank"
        unique_together = ("question", "subject_education_level")


class QuestionSubjectCountry(BaseModel):
    question_subject = models.ForeignKey(
        QuestionSubject, on_delete=models.CASCADE, related_name="subject_countries"
    )
    country = models.ForeignKey("lookups.Country", on_delete=models.CASCADE)

    class Meta:
        app_label = "questionbank"
