from django.db import models
from django.db.models import Count, F, Prefetch, Q, QuerySet

from core.models import BaseModel

# ---------------------------------------------------------------------------- #
#                               QUESTION LOOKUPS                               #
# ---------------------------------------------------------------------------- #

MEDIA_MODEL = "lookups.Media"


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

    class Meta:
        app_label = "questionbank"

    @property
    def full_name(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        self.slug = self.name.lower().replace(" ", "-")
        super().save(*args, **kwargs)

    @classmethod
    def select_random_subjects(
        cls,
        subject_question_count: dict[str, int] | None = None,
        subject_count: int | None = None,
        education_level_id: int | None = None,
    ) -> list[int]:
        """
        Select random subjects which have atleast one question based on subject count and question count.

        Args:
            subject_question_count (dict[str, int]) | None: Dictionary containing subject id as key and question count as value.
            subject_count (int) | None: Number of subjects to be selected.
            education_level_id (int) | None: Education level id.

        Returns:
            List[int]: List of random subject ids.

        """
        q_filter = Q()
        if education_level_id:
            q_filter &= Q(education_level_id=education_level_id)
        if subject_question_count:
            q_filter &= Q(Q(question_count__gt=max(subject_question_count.values())))

        return list(
            Subject.get_random(
                count=subject_count,
                q_filter=q_filter,
                annotation={
                    "question_count": Count("subjecteducationlevel__questions"),
                    "education_level_id": F("subjecteducationlevel__education_level"),
                },
            ).values_list("id", flat=True)
        )


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
    text = models.TextField(null=True, blank=True)

    subject_education_levels = models.ManyToManyField(
        "SubjectEducationLevel",
        through="QuestionSubject",
        related_name="questions",
    )

    type = models.ForeignKey(QuestionType, on_delete=models.CASCADE)

    tags = models.ManyToManyField(
        "lookups.Tag", related_name="questions", through="QuestionTag"
    )

    max_retries = models.IntegerField(default=0)
    retry_penalty = models.IntegerField(default=0)

    can_shuffle = models.BooleanField(default=False)
    has_media = models.BooleanField(default=False)

    medias = models.ManyToManyField(
        MEDIA_MODEL, related_name="questions", through="QuestionMedia"
    )

    class Meta:
        app_label = "questionbank"

    @property
    def type_name(self):
        return self.type.name

    @classmethod
    def get_detail_queryset(cls) -> QuerySet:

        return cls.objects.all().prefetch_related(
            "tags",
            "choices",
            "attempt_responses",
            "retry_hints",
            "questionmedia_set",
            "questionmedia_set__media",
            "type",
            Prefetch(
                "subjects",
                queryset=QuestionSubject.objects.select_related(
                    "subject_education_level",
                    "difficulty_level",
                    "measuring_unit",
                    "subject_education_level__subject",
                    "subject_education_level__education_level",
                ).prefetch_related("countries"),
            ),
        )

    @classmethod
    def get_questions_for_countries(cls, country_ids: list):

        return (
            cls.get_detail_queryset()
            .filter(subjects__subject_countries__country_id__in=country_ids)
            .distinct()
        )

    @classmethod
    def get_questions_for_subjects(cls, subject_ids: list):

        return (
            cls.get_detail_queryset()
            .filter(subjects__subject_education_level__subject_id__in=subject_ids)
            .distinct()
        )

    @classmethod
    def select_random_questions(
        cls,
        education_level_id: int | None = None,
        subject_id: int | str | None = None,
        question_count: int | None = None,
    ):
        """
        Select random questions based on the given subject and education level.

        Args:
            education_level_id (int): Education level id.
            subject_id (int | str): Subject id.
            question_count (int): Number of questions to be selected.

        Returns:
            List[int]: List of random question ids.
        """
        q_filter = Q()
        if education_level_id:
            q_filter &= Q(subject_education_levels__education_level=education_level_id)
        if subject_id:
            q_filter &= Q(subject_education_levels__subject=subject_id)

        return list(
            cls.get_random(
                count=question_count,
                q_filter=q_filter,
            ).values_list("id", flat=True)
        )


class QuestionChoice(BaseModel):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    title = models.CharField(max_length=255)
    text = models.TextField(blank=True, null=True)
    weight = models.IntegerField(default=0)

    is_negative_weight = models.BooleanField(default=False)
    is_correct = models.BooleanField(default=False)

    has_media = models.BooleanField(default=False)

    medias = models.ManyToManyField(
        MEDIA_MODEL, related_name="choices", through="QuestionChoiceMedia"
    )

    class Meta:
        app_label = "questionbank"

    def save(self, *args, **kwargs):
        if self.pk:
            if self.medias.exists():
                self.has_media = True
            else:
                self.has_media = False
        return super().save(*args, **kwargs)


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

    medias = models.ManyToManyField(
        MEDIA_MODEL,
        related_name="retry_hints",
        through="QuestionRetryHintMedia",
    )

    def save(self, *args, **kwargs):
        if self.pk:
            if self.medias.exists():
                self.has_media = True
            else:
                self.has_media = False
        return super().save(*args, **kwargs)

    class Meta:
        app_label = "questionbank"


# ---------------------------------------------------------------------------- #
#                                   MAPPINGS                                   #
# ---------------------------------------------------------------------------- #


class SubjectEducationLevel(BaseModel):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
    )
    education_level = models.ForeignKey(EducationLevel, on_delete=models.CASCADE)

    class Meta:
        app_label = "questionbank"
        db_table = "questionbank_subject_educationlevel"


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
        db_table = "questionbank_questionsubject_country"


class QuestionMedia(BaseModel):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
    )
    media = models.ForeignKey(MEDIA_MODEL, on_delete=models.CASCADE)

    class Meta:
        app_label = "questionbank"
        db_table = "questionbank_question_media"


class QuestionTag(BaseModel):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
    )
    tag = models.ForeignKey("lookups.Tag", on_delete=models.CASCADE)

    class Meta:
        app_label = "questionbank"
        db_table = "questionbank_question_tag"


class QuestionChoiceMedia(BaseModel):
    question_choice = models.ForeignKey(
        QuestionChoice,
        on_delete=models.CASCADE,
    )
    media = models.ForeignKey(MEDIA_MODEL, on_delete=models.CASCADE)

    class Meta:
        app_label = "questionbank"
        db_table = "questionbank_questionchoice_media"


class QuestionRetryHintMedia(BaseModel):
    question_retry_hint = models.ForeignKey(
        QuestionRetryHint,
        on_delete=models.CASCADE,
    )
    media = models.ForeignKey(MEDIA_MODEL, on_delete=models.CASCADE)

    class Meta:
        app_label = "questionbank"
        db_table = "questionbank_questionretryhint_media"
