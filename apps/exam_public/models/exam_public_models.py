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
    exam_backlog = models.ForeignKey("exam_public.ExamBacklog", on_delete=models.CASCADE)
    schedule = models.ForeignKey("exam_admin.Schedule", on_delete=models.CASCADE)
    obtained_marks = models.PositiveIntegerField(default=0)

    # ? To be filled from schedule
    date = models.DateField(auto_now=False, auto_now_add=False)
    start_time = models.TimeField(auto_now=False, auto_now_add=False, null=True)
    end_time = models.TimeField(auto_now=False, auto_now_add=False, null=True)
    waiting_duration = models.PositiveIntegerField(null=True)
    extra_duration = models.PositiveIntegerField(null=True)

    class Meta:
        app_label = "exam_public"


class CandidateExamAnswer(BaseModel):
    candidate_exam = models.ForeignKey("exam_public.CandidateExam", on_delete=models.CASCADE)
    exam_backlog_question = models.ForeignKey("exam_public.ExamBacklogQuestion", on_delete=models.CASCADE)
    exam_backlog_question_choice = models.ForeignKey("exam_public.ExamBacklogQuestionChoice", on_delete=models.CASCADE, null=True)

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
