from django.db import models

from core.models import BaseModel


class UserExamQuestionBacklog(BaseModel):
    user_exam = models.ForeignKey("exam.UserExam", on_delete=models.CASCADE)
    subject = models.ForeignKey("questionbank.Subject", on_delete=models.CASCADE)
    # * Question Fields
    question = models.ForeignKey("questionbank.Question", on_delete=models.CASCADE)
    type = models.ForeignKey("questionbank.QuestionType", on_delete=models.CASCADE)
    difficulty = models.ForeignKey(
        "questionbank.DifficultyLevel", on_delete=models.CASCADE
    )
    measuring_unit = models.ForeignKey(
        "lookups.MeasuringUnit", on_delete=models.CASCADE
    )


class UserExamQuestionChoiceBacklog(BaseModel):
    user_exam_question_backlog = models.ForeignKey(
        UserExamQuestionBacklog, on_delete=models.CASCADE
    )
    # * Question Choice Fields
    question_choice = models.ForeignKey(
        "questionbank.QuestionChoice", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
