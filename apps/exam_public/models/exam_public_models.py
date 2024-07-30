from django.db import models

from core.models import BaseModel

MEDIA_MODEL = "lookups.Media"


class Candidate(BaseModel):
    user = models.OneToOneField("user.BaseUser", on_delete=models.CASCADE)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_candidate"


class CandidateExam(BaseModel):
    candidate = models.ForeignKey("exam_public.Candidate", on_delete=models.CASCADE)
    exam = models.ForeignKey("exam_admin.Exam", on_delete=models.CASCADE)
    schedule = models.ForeignKey("exam_admin.Schedule", on_delete=models.CASCADE)
    obtained_marks = models.PositiveIntegerField(default=0)

    # ? To be filled from exam
    education_level = models.ForeignKey("questionbank.EducationLevel", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10, blank=True)
    abbreviation = models.CharField(max_length=10, blank=True)
    instructions = models.TextField(blank=True)

    total_marks = models.PositiveIntegerField(default=0)
    pass_marks = models.PositiveIntegerField(default=0)

    date = models.DateField(auto_now=False, auto_now_add=False)
    start_time = models.TimeField(auto_now=False, auto_now_add=False, null=True)
    end_time = models.TimeField(auto_now=False, auto_now_add=False, null=True)
    waiting_duration = models.PositiveIntegerField(null=True)
    extra_duration = models.PositiveIntegerField(null=True)

    is_global = models.BooleanField(default=True)

    class Meta:
        app_label = "exam_public"


class CandidateExamAnswer(BaseModel):
    canidate_exam_question_backlog = models.ForeignKey("exam_public.CandidateExamQuestionBacklog", on_delete=models.CASCADE)
    candidate_exam_question_backlog_choice = models.ForeignKey("exam_public.CandidateExamQuestionBacklogChoice", on_delete=models.CASCADE, null=True)

    answer_text = models.TextField(blank=True)
    answer_files = models.ManyToManyField(MEDIA_MODEL, through="exam_public.CandidateExamAnswerMedia")

    score = models.FloatField(default=0)
    is_correct = models.BooleanField(default=False)
    seconds_taken = models.IntegerField(default=0)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_candidateexam_answer"


# ---------------------------------------------------------------------------- #
#                                   MAPPINGS                                   #
# ---------------------------------------------------------------------------- #


class CandidateExamAnswerMedia(BaseModel):
    candidate_exam_answer = models.ForeignKey(CandidateExamAnswer, on_delete=models.CASCADE)
    media = models.ForeignKey(MEDIA_MODEL, on_delete=models.CASCADE)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_candidateexam_answer_media"
