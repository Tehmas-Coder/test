from django.db import models
from core.models import BaseModel


# ---------------------------------------------------------------------------- #
#                               QUESTION LOOKUPS                               #
# ---------------------------------------------------------------------------- #
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

    tags = models.ManyToManyField("lookups.Tag", related_name="questions")

    max_retries = models.IntegerField(default=0)
    retry_penalty = models.IntegerField(default=0)

    can_shuffle = models.BooleanField(default=False)
    has_media = models.BooleanField(default=False)

    class Meta:
        app_label = "questionbank"


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

    class Meta:
        app_label = "questionbank"


class QuestionAttemptResponse(BaseModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
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
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.TextField()
    has_media = models.BooleanField(default=False)

    class Meta:
        app_label = "questionbank"


# ---------------------------------------------------------------------------- #
#                                   MAPPINGS                                   #
# ---------------------------------------------------------------------------- #


class SubjectEducationLevel(BaseModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    education_level = models.ForeignKey(EducationLevel, on_delete=models.CASCADE)

    class Meta:
        app_label = "questionbank"


class QuestionSubject(BaseModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    subject_education_level = models.ForeignKey(
        SubjectEducationLevel, on_delete=models.CASCADE
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
    question_subject = models.ForeignKey(QuestionSubject, on_delete=models.CASCADE)
    country = models.ForeignKey("lookups.Country", on_delete=models.CASCADE)

    class Meta:
        app_label = "questionbank"
