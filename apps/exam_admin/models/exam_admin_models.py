from django.db import models
from django.db.models import Prefetch, Q, QuerySet

from apps.questionbank.models import Question
from core.models import BaseModel


# ---------------------------------------------------------------------------- #
#                                  EXAM BASIC                                  #
# ---------------------------------------------------------------------------- #
class Schedule(BaseModel):
    title = models.CharField(max_length=255, blank=True)
    start_datetime = models.DateTimeField(auto_now=False, auto_now_add=False)
    end_datetime = models.DateTimeField(auto_now=False, auto_now_add=False)
    waiting_duration = models.PositiveIntegerField(null=True)
    extra_duration = models.PositiveIntegerField(null=True)

    class Meta:
        app_label = "exam_admin"


class Section(BaseModel):
    exam = models.ForeignKey("exam_admin.Exam", on_delete=models.CASCADE, related_name="sections")
    measuring_unit = models.ForeignKey("lookups.MeasuringUnit", on_delete=models.CASCADE, related_name="sections_measuring_unit")

    title = models.CharField(max_length=255)
    sequence = models.PositiveIntegerField(default=1)
    time_limit = models.PositiveIntegerField(null=True)

    is_global = models.BooleanField(default=True)
    is_shuffle = models.BooleanField(default=False)

    class Meta:
        app_label = "exam_admin"


class SubSection(BaseModel):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="subsections")
    measuring_unit = models.ForeignKey("lookups.MeasuringUnit", on_delete=models.CASCADE, related_name="subsections_measuring_unit")

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
    education_level = models.ForeignKey("questionbank.EducationLevel", on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10, blank=True)
    abbreviation = models.CharField(max_length=10, blank=True)
    instructions = models.TextField(blank=True, null=True)
    total_marks = models.PositiveIntegerField(default=0)
    pass_marks = models.PositiveIntegerField(default=0)

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
    def get_detail_queryset(cls) -> QuerySet:
        return (
            cls.objects.all()
            .select_related("education_level")
            .prefetch_related(
                Prefetch(
                    "examsubject_set",
                    queryset=ExamSubject.objects.all()
                    .select_related(
                        "subject_education_level",
                        "subject_education_level__subject",
                        "subject_education_level__education_level",
                    )
                    .prefetch_related(
                        Prefetch(
                            "examsubjectquestion_set",
                            queryset=ExamSubjectQuestion.objects.all()
                            .select_related(
                                "section",
                                "subsection",
                            )
                            .prefetch_related(
                                Prefetch("question", queryset=Question.get_detail_queryset()),
                            ),
                        ),
                    ),
                ),
                Prefetch(
                    "sections",
                    Section.objects.all().prefetch_related("subsections"),
                ),
            )
        )


# ---------------------------------------------------------------------------- #
#                                   MAPPINGS                                   #
# ---------------------------------------------------------------------------- #


class ExamSubject(BaseModel):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    subject_education_level = models.ForeignKey("questionbank.SubjectEducationLevel", on_delete=models.CASCADE)

    questions = models.ManyToManyField("questionbank.Question", through="ExamSubjectQuestion")

    class Meta:
        app_label = "exam_admin"
        db_table = "exam_admin_examsubject"


class ExamSubjectQuestion(BaseModel):
    exam_subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE)
    question = models.ForeignKey("questionbank.Question", on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, related_name="questions")
    subsection = models.ForeignKey(SubSection, on_delete=models.CASCADE, null=True, related_name="questions")

    total_marks = models.PositiveIntegerField(default=0)
    sequence = models.PositiveIntegerField(default=1)

    class Meta:
        app_label = "exam_admin"
        db_table = "exam_admin_examsubject_question"


class ExamSubjectCountry(BaseModel):
    exam_subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE, related_name="subject_countries")
    country = models.ForeignKey("lookups.Country", on_delete=models.CASCADE)

    class Meta:
        app_label = "exam_admin"
        db_table = "exam_admin_examsubject_country"
