from django.db import models
from django.db.models import Q, QuerySet

from apps.exam_admin.helpers.queryset_functions import get_exam_detailed_queryset
from apps.user.utils.user_utils import get_current_user_organization
from core.models import BaseModel
from middlewares.current_user_middleware import get_current_user


# ---------------------------------------------------------------------------- #
#                                  EXAM BASIC                                  #
# ---------------------------------------------------------------------------- #
class Schedule(BaseModel):
    """
    Represents a schedule for exams.

    - id: Autofield (PK)
    - organization: Organization (FK)
    - title: CharField
    - start_datetime: DateTimeField
    - end_datetime: DateTimeField
    - waiting_duration: PositiveIntegerField
    - extra_duration: PositiveIntegerField
    """

    organization = models.ForeignKey("lookups.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="organization_schedules")

    title = models.CharField(max_length=255, blank=True)
    start_datetime = models.DateTimeField(auto_now=False, auto_now_add=False)
    end_datetime = models.DateTimeField(auto_now=False, auto_now_add=False)
    waiting_duration = models.PositiveIntegerField(null=True)
    extra_duration = models.PositiveIntegerField(null=True)

    def save(self, *args, **kwargs):
        """
        On Creation of Schedule, set the organization_id to the current user's organization if the user is not a superuser and then save the Schedule.
        """
        if not self.pk:
            if not get_current_user().is_superuser:  # type: ignore
                self.organization_id = get_current_user_organization()
        return super().save(*args, **kwargs)

    class Meta:
        app_label = "exam_admin"


class Section(BaseModel):
    """
    Represents a section within an exam.

    - id: Autofield (PK)
    - exam: Exam (FK)
    - measuring_unit: MeasuringUnit (FK)
    - title: CharField
    - sequence: PositiveIntegerField
    - time_limit: PositiveIntegerField
    - is_global: BooleanField
    - is_shuffle: BooleanField
    """

    exam = models.ForeignKey("exam_admin.Exam", on_delete=models.CASCADE, related_name="sections")
    measuring_unit = models.ForeignKey("lookups.MeasuringUnit", on_delete=models.PROTECT, related_name="sections_measuring_unit")

    title = models.CharField(max_length=255)
    sequence = models.PositiveIntegerField(default=1)
    time_limit = models.PositiveIntegerField(null=True)

    is_global = models.BooleanField(default=True)
    is_shuffle = models.BooleanField(default=False)

    class Meta:
        app_label = "exam_admin"


class SubSection(BaseModel):
    """
    Represents a subsection within a section.

    - id: Autofield (PK)
    - section: Section (FK)
    - measuring_unit: MeasuringUnit (FK)
    - title: CharField
    - sequence: PositiveIntegerField
    - time_limit: PositiveIntegerField
    - is_global: BooleanField
    - is_shuffle: BooleanField
    """

    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="subsections")
    measuring_unit = models.ForeignKey("lookups.MeasuringUnit", on_delete=models.PROTECT, related_name="subsections_measuring_unit")

    title = models.CharField(max_length=255)
    sequence = models.PositiveIntegerField(default=1)
    time_limit = models.PositiveIntegerField(null=True)

    is_global = models.BooleanField(default=True)
    is_shuffle = models.BooleanField(default=False)

    class Meta:
        app_label = "exam_admin"


# ---------------------------------------------------------------------------- #
#                                     EXAM                                     #
# ---------------------------------------------------------------------------- #
class Exam(BaseModel):
    """
    Represents an exam.

    - id: Autofield (PK)
    - organization: Organization (FK)
    - education_level: EducationLevel (FK)
    - name: CharField
    - code: CharField
    - abbreviation: CharField
    - instructions: TextField
    - total_marks: PositiveIntegerField
    - passing_percentage: PositiveIntegerField
    - exam_status: CharField
        Choices:
            - "draft"
            - "active"
    - is_public: BooleanField
    - is_global: BooleanField
    - subjects: SubjectEducationLevel (M2M)
    """

    organization = models.ForeignKey("lookups.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="organization_exams")
    education_level = models.ForeignKey("questionbank.EducationLevel", on_delete=models.PROTECT)

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10, blank=True)
    abbreviation = models.CharField(max_length=10, blank=True)
    instructions = models.TextField(blank=True, null=True)
    total_marks = models.PositiveIntegerField(default=0)
    passing_percentage = models.PositiveIntegerField(default=0)
    TYPE_CHOICES = (
        ("draft", "Draft"),
        ("active", "Active"),
    )
    exam_status = models.CharField(max_length=100, choices=TYPE_CHOICES, default="draft")

    is_public = models.BooleanField(default=False)
    is_global = models.BooleanField(default=True)

    subjects = models.ManyToManyField("questionbank.SubjectEducationLevel", through="ExamSubject")

    class Meta:
        app_label = "exam_admin"

    @classmethod
    def get_detail_queryset(
        cls, sections=False, exam_subject=False, exam_subject_questions=False, exam_subject_questions_question=False, all=False, q_filter=Q()
    ) -> QuerySet:
        return get_exam_detailed_queryset(cls, sections, exam_subject, exam_subject_questions, exam_subject_questions_question, all, q_filter)


# ---------------------------------------------------------------------------- #
#                                   MAPPINGS                                   #
# ---------------------------------------------------------------------------- #
class ExamSubject(BaseModel):
    """
    Represents a mapping between exams and subjects.

    - id: Autofield (PK)
    - exam: Exam (FK)
    - subject_education_level: SubjectEducationLevel (FK)
    - questions: Question (M2M)
    """

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    subject_education_level = models.ForeignKey("questionbank.SubjectEducationLevel", on_delete=models.CASCADE)

    questions = models.ManyToManyField("questionbank.Question", through="ExamSubjectQuestion")

    class Meta:
        app_label = "exam_admin"
        db_table = "exam_admin_examsubject"


class ExamSubjectQuestion(BaseModel):
    """
    Represents a mapping between exam subjects and questions.

    - id: Autofield (PK)
    - exam_subject: ExamSubject (FK)
    - question: Question (FK)
    - section: Section (FK)
    - subsection: SubSection (FK)
    - total_marks: PositiveIntegerField
    - sequence: PositiveIntegerField
    """

    exam_subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE)
    question = models.ForeignKey("questionbank.Question", on_delete=models.PROTECT)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, related_name="questions")
    subsection = models.ForeignKey(SubSection, on_delete=models.CASCADE, null=True, related_name="questions")

    total_marks = models.PositiveIntegerField(default=0)
    sequence = models.PositiveIntegerField(default=1)

    class Meta:
        app_label = "exam_admin"
        db_table = "exam_admin_examsubject_question"


class ExamSubjectCountry(BaseModel):
    """
    Represents a mapping between exam subjects and countries.

    - id: Autofield (PK)
    - exam_subject: ExamSubject (FK)
    - country: Country (FK)
    """

    exam_subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE, related_name="subject_countries")
    country = models.ForeignKey("lookups.Country", on_delete=models.CASCADE)

    class Meta:
        app_label = "exam_admin"
        db_table = "exam_admin_examsubject_country"
