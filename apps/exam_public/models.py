from django.db import models

from core.models import BaseModel

MEDIA_MODEL = "lookups.Media"


class Candidate(BaseModel):
    user = models.OneToOneField("user.BaseUser", on_delete=models.CASCADE)

    class Meta:
        app_label = "exam_public"
        db_table = "exam_public_candidate"


class CandidateExamAnswer(BaseModel):
    canidate_exam_question_backlog = models.ForeignKey("exam_admin.CandidateExamQuestionBacklog", on_delete=models.CASCADE)
    candidate_exam_question_backlog_choice = models.ForeignKey("exam_admin.CandidateExamQuestionBacklogChoice", on_delete=models.CASCADE, null=True)

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
