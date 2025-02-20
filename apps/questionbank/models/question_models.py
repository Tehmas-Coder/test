from django.db import IntegrityError, models
from django.db.models import Count, F, Q, QuerySet
from django.utils.text import slugify

from apps.questionbank.helpers.queryset_functions import get_question_detailed_queryset
from apps.user.utils.user_utils import get_current_user_organization
from core.models import BaseModel
from middlewares.current_user_middleware import get_current_user
from middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import make_error_response

# ---------------------------------------------------------------------------- #
#                               QUESTION LOOKUPS                               #
# ---------------------------------------------------------------------------- #

MEDIA_MODEL = "user.Media"


class Tag(BaseModel):
    """
    Represents a tag that can be assigned to questions.

    - id: Autofield (PK)
    - organization: Organization (FK)
    - name: CharField
    - code: CharField
    - abbreviation: CharField
    """

    organization = models.ForeignKey("lookups.Organization", on_delete=models.CASCADE, null=True, blank=True)

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        if not self.pk:
            if not get_current_user().is_superuser:  # type: ignore
                self.organization_id = get_current_user_organization()
        return super().save(*args, **kwargs)

    class Meta:
        app_label = "questionbank"


class EducationLevel(BaseModel):
    """
    Represents an education level that can be assigned to subjects.

    - id: Autofield (PK)
    - organization: Organization (FK)
    - name: CharField
    - slug: SlugField
    - code: CharField
    - abbreviation: CharField
    """

    organization = models.ForeignKey("lookups.Organization", on_delete=models.CASCADE, null=True, blank=True)

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    code = models.CharField(max_length=10)
    abbreviation = models.CharField(max_length=10, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.slug = slugify(f"{self.organization_id}-{self.name}" if self.organization else slugify(self.name))  # type: ignore
        try:
            super().save(*args, **kwargs)
        except IntegrityError:
            ResponseMiddleware.return_now(make_error_response(message="Education level with this name already exists"))

    class Meta:
        app_label = "questionbank"


class Subject(BaseModel):
    """
    Represents a subject that can be assigned to questions.

    - id: Autofield (PK)
    - organization: Organization (FK)
    - name: CharField
    - slug: SlugField
    - code: CharField
    - abbreviation: CharField
    """

    organization = models.ForeignKey("lookups.Organization", on_delete=models.CASCADE, null=True, blank=True)

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    code = models.CharField(max_length=10)
    abbreviation = models.CharField(max_length=10, blank=True)

    class Meta:
        app_label = "questionbank"

    @property
    def full_name(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.slug = slugify(f"{self.organization_id}-{self.name}" if self.organization else slugify(self.name))  # type: ignore
        try:
            super().save(*args, **kwargs)
        except IntegrityError:
            ResponseMiddleware.return_now(make_error_response(message="Subject with this name already exists"))

    @classmethod
    def select_random_subjects(
        cls,
        subject_question_count: dict[str, int] | None = None,
        subject_count: int | None = None,
        education_level_id: int | None = None,
    ) -> list[int]:
        """
        Select random subjects which have at least one question based on subject count and question count.

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
    """
    Represents a type of question.

    - id: Autofield (PK)
    - name: CharField
    - slug: SlugField
    - abbreviation: CharField
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    abbreviation = models.CharField(max_length=10, blank=True)

    def save(self, *args, **kwargs):
        self.slug = self.name.lower().replace(" ", "-")
        super().save(*args, **kwargs)

    class Meta:
        app_label = "questionbank"


class DifficultyLevel(BaseModel):
    """
    Represents a difficulty level for questions.

    - id: Autofield (PK)
    - name: CharField
    - slug: SlugField
    - code: CharField
    - abbreviation: CharField
    - sequence: IntegerField
    """

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
    """
    Represents a question in the system.

    - id: Autofield (PK)
    - type: QuestionType (FK)
    - organization: Organization (FK)
    - title: TextField
    - text: TextField
    - max_retries: IntegerField
    - retry_penalty: IntegerField
    - can_shuffle: BooleanField
    - has_media: BooleanField
    - is_public: BooleanField
    - tags: Tag (M2M)
    - medias: Media (M2M)
    - subject_education_levels: SubjectEducationLevel (M2M)
    """

    type = models.ForeignKey(QuestionType, on_delete=models.CASCADE)
    organization = models.ForeignKey("lookups.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="organization_questions")

    title = models.TextField()
    text = models.TextField(null=True, blank=True)
    max_retries = models.IntegerField(default=0)
    retry_penalty = models.IntegerField(default=0)

    can_shuffle = models.BooleanField(default=False)
    has_media = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)

    tags = models.ManyToManyField("questionbank.Tag", related_name="questions", through="QuestionTag")
    medias = models.ManyToManyField(MEDIA_MODEL, related_name="questions", through="QuestionMedia")
    subject_education_levels = models.ManyToManyField("SubjectEducationLevel", through="QuestionSubject", related_name="questions")

    class Meta:
        app_label = "questionbank"

    @property
    def type_name(self):
        return self.type.name

    @classmethod
    def get_detail_queryset(
        cls, q_filter=Q(), tags=False, attempt_responses=False, choices=False, retry_hints=False, subjects=False, all=False
    ) -> QuerySet:
        return get_question_detailed_queryset(cls, q_filter, tags, attempt_responses, choices, retry_hints, subjects, all)

    @classmethod
    def get_questions_for_countries(cls, country_ids: list):
        return (
            cls.get_detail_queryset()
            .filter(
                subjects__subject_countries__country_id__in=country_ids,
            )
            .distinct()
        )

    @classmethod
    def get_questions_for_subjects(cls, subject_ids: list):
        return (
            cls.get_detail_queryset()
            .filter(
                subjects__subject_education_level__subject_id__in=subject_ids,
            )
            .distinct()
        )

    @classmethod
    def get_questions_for_subjects_and_education_levels(cls, subject_ids: list, education_level_ids: list):
        return (
            cls.get_detail_queryset()
            .filter(
                subjects__subject_education_level__subject_id__in=subject_ids,
                subjects__subject_education_level__education_level_id__in=education_level_ids,
            )
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
    """
    Represents a choice for a question.

    - id: Autofield (PK)
    - question: Question (FK)
    - title: CharField
    - text: TextField
    - weight: IntegerField
    - is_negative_weight: BooleanField
    - is_correct: BooleanField
    - has_media: BooleanField
    - medias: Media (M2M)
    """

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")

    title = models.CharField(max_length=255)
    text = models.TextField(blank=True, null=True)
    weight = models.IntegerField(default=0)

    is_negative_weight = models.BooleanField(default=False)
    is_correct = models.BooleanField(default=False)
    has_media = models.BooleanField(default=False)

    medias = models.ManyToManyField(MEDIA_MODEL, related_name="choices", through="QuestionChoiceMedia")

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
    """
    Represents an attempt response for a question.

    - id: Autofield (PK)
    - question: Question (FK)
    - text: TextField
    - type: CharField (choices are [correct, wrong, partial, skipped, unanswered])
    """

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="attempt_responses")
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
        app_label = "questionbank"


class QuestionRetryHint(BaseModel):
    """
    Represents a retry hint for a question.

    - id: Autofield (PK)
    - question: Question (FK)
    - text: TextField
    - sequence: IntegerField
    - has_media: BooleanField
    - medias: Media (M2M)
    """

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="retry_hints")

    text = models.TextField(null=True, blank=True)
    sequence = models.IntegerField(default=1)

    has_media = models.BooleanField(default=False)

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


class SubjectEducationLevel(BaseModel):
    """
    Represents a mapping between subjects and education levels.

    - id: Autofield (PK)
    - organization: Organization (FK)
    - subject: Subject (FK)
    - education_level: EducationLevel (FK)
    """

    organization = models.ForeignKey("lookups.Organization", on_delete=models.CASCADE, null=True, blank=True)

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    education_level = models.ForeignKey(EducationLevel, on_delete=models.CASCADE)

    class Meta:
        app_label = "questionbank"
        db_table = "questionbank_subject_educationlevel"

    def save(self, *args, **kwargs):
        if not self.pk:
            if (not get_current_user().is_superuser) and (self.subject.organization or self.education_level.organization):  # type: ignore
                self.organization_id = get_current_user_organization()
        return super().save(*args, **kwargs)

    @classmethod
    def get_detail_queryset(cls):
        return cls.objects.get_queryset().select_related(
            "organization",
            "subject",
            "education_level",
        )


class QuestionSubject(BaseModel):
    """
    Represents a mapping between questions and subjects.

    - id: Autofield (PK)
    - question: Question (FK)
    - subject_education_level: SubjectEducationLevel (FK)
    - difficulty_level: DifficultyLevel (FK)
    - measuring_unit: MeasuringUnit (FK)
    - time_limit: IntegerField
    - total_marks: IntegerField
    - is_optional: BooleanField
    - is_global: BooleanField
    - countries: Country (M2M)
    """

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="subjects")
    subject_education_level = models.ForeignKey(SubjectEducationLevel, on_delete=models.CASCADE, related_name="question_subjects")
    difficulty_level = models.ForeignKey(DifficultyLevel, on_delete=models.CASCADE)
    measuring_unit = models.ForeignKey("lookups.MeasuringUnit", on_delete=models.CASCADE)

    time_limit = models.IntegerField(default=0)
    total_marks = models.IntegerField(default=0)

    is_optional = models.BooleanField(default=False)
    is_global = models.BooleanField(default=False)

    countries = models.ManyToManyField("lookups.Country", through="QuestionSubjectCountry")

    class Meta:
        app_label = "questionbank"
        unique_together = ("question", "subject_education_level")


class QuestionSubjectCountry(BaseModel):
    """
    Represents a mapping between question subjects and countries.

    - id: Autofield (PK)
    - question_subject: QuestionSubject (FK)
    - country: Country (FK)
    """

    question_subject = models.ForeignKey(QuestionSubject, on_delete=models.CASCADE, related_name="subject_countries")
    country = models.ForeignKey("lookups.Country", on_delete=models.CASCADE)

    class Meta:
        app_label = "questionbank"
        db_table = "questionbank_questionsubject_country"


class QuestionMedia(BaseModel):
    """
    Represents a mapping between questions and media.

    - id: Autofield (PK)
    - question: Question (FK)
    - media: Media (FK)
    """

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    media = models.ForeignKey(MEDIA_MODEL, on_delete=models.CASCADE)

    class Meta:
        app_label = "questionbank"
        db_table = "questionbank_question_media"


class QuestionTag(BaseModel):
    """
    Represents a mapping between questions and tags.

    - id: Autofield (PK)
    - question: Question (FK)
    - tag: Tag (FK)
    """

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    tag = models.ForeignKey("questionbank.Tag", on_delete=models.CASCADE)

    class Meta:
        app_label = "questionbank"
        db_table = "questionbank_question_tag"


class QuestionChoiceMedia(BaseModel):
    """
    Represents a mapping between question choices and media.

    - id: Autofield (PK)
    - question_choice: QuestionChoice (FK)
    - media: Media (FK)
    """

    question_choice = models.ForeignKey(QuestionChoice, on_delete=models.CASCADE)
    media = models.ForeignKey(MEDIA_MODEL, on_delete=models.CASCADE)

    class Meta:
        app_label = "questionbank"
        db_table = "questionbank_questionchoice_media"


class QuestionRetryHintMedia(BaseModel):
    """
    Represents a mapping between question retry hints and media.

    - id: Autofield (PK)
    - question_retry_hint: QuestionRetryHint (FK)
    - media: Media (FK)
    """

    question_retry_hint = models.ForeignKey(QuestionRetryHint, on_delete=models.CASCADE)
    media = models.ForeignKey(MEDIA_MODEL, on_delete=models.CASCADE)

    class Meta:
        app_label = "questionbank"
        db_table = "questionbank_questionretryhint_media"
