from django.db import models

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
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    sequence = models.PositiveIntegerField(default=1)

    time_limit = models.PositiveIntegerField(null=True)
    total_marks = models.PositiveIntegerField(default=0)
    passing_marks = models.PositiveIntegerField(null=True)

    subsections = models.ManyToManyField("exam.SubSection", through="SectionSubSection")
    questions = models.ManyToManyField(
        "questionbank.Question", through="ExamSubjectQuestion"
    )

    is_global = models.BooleanField(default=True)
    is_shuffle = models.BooleanField(default=False)
    is_negative_marking = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.slug = self.title.lower().replace(" ", "-")
        super().save(*args, **kwargs)

    class Meta:
        app_label = "exam"


class SubSection(BaseModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    sequence = models.PositiveIntegerField(default=1)

    time_limit = models.PositiveIntegerField(null=True)
    total_marks = models.PositiveIntegerField(default=0)
    passing_marks = models.PositiveIntegerField(null=True)

    questions = models.ManyToManyField(
        "questionbank.Question", through="ExamSubjectQuestion"
    )

    is_global = models.BooleanField(default=True)
    is_shuffle = models.BooleanField(default=False)
    is_negative_marking = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.slug = self.title.lower().replace(" ", "-")
        super().save(*args, **kwargs)

    class Meta:
        app_label = "exam"


class SectionSubSection(BaseModel):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    sub_section = models.ForeignKey(SubSection, on_delete=models.CASCADE)


# ---------------------------------------------------------------------------- #
#                                     EXAM                                     #
# ---------------------------------------------------------------------------- #


class Exam(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10)
    abbreviation = models.CharField(max_length=10)
    instructions = models.TextField()

    education_level = models.ForeignKey(
        "questionbank.EducationLevel", on_delete=models.CASCADE
    )

    total_marks = models.PositiveIntegerField(default=0)
    pass_marks = models.PositiveIntegerField(default=0)

    subjects = models.ManyToManyField("questionbank.Subject", through="ExamSubject")

    is_global = models.BooleanField(default=True)

    class Meta:
        app_label = "exam"


class UserExam(BaseModel):
    user = models.ForeignKey("users.BaseUser", on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    obtained_marks = models.PositiveIntegerField(default=0)

    # ? To be filled from exam
    education_level = models.ForeignKey(
        "questionbank.EducationLevel", on_delete=models.CASCADE
    )
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

    class Meta:
        app_label = "exam"
        db_table = "exam_examsubject"


class ExamSubjectQuestion(BaseModel):
    exam_subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE)
    question = models.ForeignKey("questionbank.Question", on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    sub_section = models.ForeignKey(SubSection, on_delete=models.CASCADE)

    sequence = models.PositiveIntegerField(default=1)

    class Meta:
        app_label = "exam"
        db_table = "exam_examsubject_questions"


class ExamSubjectCountry(BaseModel):
    exam_subject = models.ForeignKey(
        ExamSubject, on_delete=models.CASCADE, related_name="subject_countries"
    )
    country = models.ForeignKey("lookups.Country", on_delete=models.CASCADE)

    class Meta:
        app_label = "exam"
        db_table = "exam_examsubject_countries"


# ---------------------------------------------------------------------------- #
#                                    ANSWER                                    #
# ---------------------------------------------------------------------------- #


class ExamAnswer(BaseModel):
    exam_subject_question = models.ForeignKey(
        ExamSubjectQuestion, on_delete=models.CASCADE, related_name="answers"
    )
    question_attempt_response = models.ForeignKey(
        "questionbank.QuestionAttemptResponse", on_delete=models.CASCADE
    )
    is_correct = models.BooleanField(default=False)

    class Meta:
        app_label = "exam"
        db_table = "exam_examanswer"
