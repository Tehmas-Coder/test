from django.db import models

from core.models import BaseModel


class CandidateExamSectionScore(BaseModel):
    candidate_exam = models.ForeignKey("exam_public.CandidateExam", on_delete=models.CASCADE)
    section_backlog = models.ForeignKey("exam_public.SectionBacklog", on_delete=models.DO_NOTHING)
    question_count = models.PositiveIntegerField(default=0)
    total_obtainable_marks = models.IntegerField(default=0)
    subsection_count = models.PositiveIntegerField(default=0)
    score = models.FloatField(default=0)

    class Meta:
        app_label = "exam_scoring"
        db_table = "exam_scoring_candidateexam_sectionbacklog_score"


class CandidateExamSubSectionScore(BaseModel):
    candidate_exam = models.ForeignKey("exam_public.CandidateExam", on_delete=models.CASCADE)
    subsection_backlog = models.ForeignKey("exam_public.SubSectionBacklog", on_delete=models.DO_NOTHING)
    question_count = models.PositiveIntegerField(default=0)
    total_obtainable_marks = models.IntegerField(default=0)
    score = models.FloatField(default=0)

    class Meta:
        app_label = "exam_scoring"
        db_table = "exam_scoring_candidateexam_subsectionbacklog_score"
