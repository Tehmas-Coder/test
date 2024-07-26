from django.db import models
from django.db.models import Prefetch, QuerySet

from apps.questionbank.models import Question
from core.models import BaseModel


# ---------------------------------------------------------------------------- #
#                                  EXAM BASIC                                  #
# ---------------------------------------------------------------------------- #
class Schedule(BaseModel):
    date = models.DateField(auto_now=False, auto_now_add=False)
    title = models.CharField(max_length=255, blank=True)
    start_time = models.TimeField(auto_now=False, auto_now_add=False)
    end_time = models.TimeField(auto_now=False, auto_now_add=False)
    waiting_duration = models.PositiveIntegerField(null=True)
    extra_duration = models.PositiveIntegerField(null=True)

    class Meta:
        app_label = "exam"


class Section(BaseModel):
    exam = models.ForeignKey("exam.Exam", on_delete=models.CASCADE, related_name="sections")
    measuring_unit = models.ForeignKey("lookups.MeasuringUnit", on_delete=models.CASCADE, related_name="sections_measuring_unit")

    title = models.CharField(max_length=255)
    sequence = models.PositiveIntegerField(default=1)

    time_limit = models.PositiveIntegerField(null=True)
    total_marks = models.PositiveIntegerField(default=0)
    passing_marks = models.PositiveIntegerField(null=True)

    is_global = models.BooleanField(default=True)
    is_shuffle = models.BooleanField(default=False)
    is_negative_marking = models.BooleanField(default=False)

    class Meta:
        app_label = "exam"


class SubSection(BaseModel):

    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="subsections")
    measuring_unit = models.ForeignKey("lookups.MeasuringUnit", on_delete=models.CASCADE, related_name="subsections_measuring_unit")

    title = models.CharField(max_length=255)
    sequence = models.PositiveIntegerField(default=1)

    time_limit = models.PositiveIntegerField(null=True)
    total_marks = models.PositiveIntegerField(default=0)
    passing_marks = models.PositiveIntegerField(null=True)

    is_global = models.BooleanField(default=True)
    is_shuffle = models.BooleanField(default=False)
    is_negative_marking = models.BooleanField(default=False)

    class Meta:
        app_label = "exam"


# ---------------------------------------------------------------------------- #
#                                     EXAM                                     #
# ---------------------------------------------------------------------------- #


class Exam(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10, blank=True)
    abbreviation = models.CharField(max_length=10, blank=True)
    instructions = models.TextField()

    education_level = models.ForeignKey("questionbank.EducationLevel", on_delete=models.CASCADE)

    total_marks = models.PositiveIntegerField(default=0)
    pass_marks = models.PositiveIntegerField(default=0)

    subjects = models.ManyToManyField("questionbank.Subject", through="ExamSubject")

    is_global = models.BooleanField(default=True)

    class Meta:
        app_label = "exam"

    @classmethod
    def get_detail_queryset(cls) -> QuerySet:
        return (
            cls.objects.all()
            .select_related("education_level")
            .prefetch_related(
                "examsubject_set",
                "examsubject_set__subject",
                Prefetch(
                    "examsubject_set__examsubjectquestion_set",
                    queryset=ExamSubjectQuestion.objects.filter(
                        section__meta_status="active",
                        subsection__meta_status="active",
                    ).select_related("section", "subsection"),
                ),
                Prefetch(
                    "sections",
                    Section.objects.filter(meta_status="active").prefetch_related("subsections"),
                ),
                Prefetch(
                    "examsubject_set__examsubjectquestion_set__question",
                    queryset=Question.get_detail_queryset(),
                ),
            )
        )


class UserExam(BaseModel):
    user = models.ForeignKey("user.BaseUser", on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    obtained_marks = models.PositiveIntegerField(default=0)

    # ? To be filled from exam
    education_level = models.ForeignKey("questionbank.EducationLevel", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10)
    abbreviation = models.CharField(max_length=10)
    instructions = models.TextField()

    total_marks = models.PositiveIntegerField(default=0)
    pass_marks = models.PositiveIntegerField(default=0)
    date = models.DateField(auto_now=False, auto_now_add=False)
    start_time = models.TimeField(auto_now=False, auto_now_add=False)
    end_time = models.TimeField(auto_now=False, auto_now_add=False)
    waiting_duration = models.PositiveIntegerField(null=True)
    extra_duration = models.PositiveIntegerField(null=True)

    is_global = models.BooleanField(default=True)

    class Meta:
        app_label = "exam"


# ---------------------------------------------------------------------------- #
#                                   MAPPINGS                                   #
# ---------------------------------------------------------------------------- #


class ExamSubject(BaseModel):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
    )
    subject = models.ForeignKey("questionbank.Subject", on_delete=models.CASCADE)

    questions = models.ManyToManyField("questionbank.Question", through="ExamSubjectQuestion")

    class Meta:
        app_label = "exam"
        db_table = "exam_examsubject"


class ExamSubjectQuestion(BaseModel):
    exam_subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE)
    question = models.ForeignKey("questionbank.Question", on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, related_name="questions")
    subsection = models.ForeignKey(SubSection, on_delete=models.CASCADE, null=True, related_name="questions")

    sequence = models.PositiveIntegerField(default=1)

    class Meta:
        app_label = "exam"
        db_table = "exam_examsubject_question"


class ExamSubjectCountry(BaseModel):
    exam_subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE, related_name="subject_countries")
    country = models.ForeignKey("lookups.Country", on_delete=models.CASCADE)

    class Meta:
        app_label = "exam"
        db_table = "exam_examsubject_country"


# ---------------------------------------------------------------------------- #
#                                    ANSWER                                    #
# ---------------------------------------------------------------------------- #


class ExamAnswer(BaseModel):
    exam_subject_question = models.ForeignKey(ExamSubjectQuestion, on_delete=models.CASCADE, related_name="answers")
    question_attempt_response = models.ForeignKey("questionbank.QuestionAttemptResponse", on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False)

    class Meta:
        app_label = "exam"
