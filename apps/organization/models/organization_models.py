from django.db import models

from core.models import BaseModel


class Organization(BaseModel):
    name = models.CharField(max_length=255)
    country = models.ForeignKey("lookups.Country", on_delete=models.CASCADE, null=True, blank=True)
    users = models.ManyToManyField("user.BaseUser", through="OrganizationUser", through_fields=("organization", "user"))
    packages = models.ManyToManyField("lookups.Package", through="OrganizationPackage")
    questions = models.ManyToManyField("questionbank.Question", through="OrganizationQuestion")
    exams = models.ManyToManyField("exam_admin.Exam", through="OrganizationExam")

    class Meta:
        app_label = "organization"
        db_table = "organization_organization"


class OrganizationUser(BaseModel):

    organization = models.ForeignKey("Organization", on_delete=models.CASCADE, related_name="organization_users")
    user = models.ForeignKey("user.BaseUser", on_delete=models.CASCADE, related_name="user_organizations")

    class Meta:
        app_label = "organization"
        db_table = "organization_organization_user"


class OrganizationQuestion(BaseModel):

    organization = models.ForeignKey("Organization", on_delete=models.CASCADE, related_name="organization_questions")
    question = models.ForeignKey("questionbank.Question", on_delete=models.DO_NOTHING)

    class Meta:
        app_label = "organization"
        db_table = "organization_organization_question"


class OrganizationExam(BaseModel):

    organization = models.ForeignKey("Organization", on_delete=models.CASCADE, related_name="organization_exams")
    exam = models.ForeignKey("exam_admin.Exam", on_delete=models.CASCADE)

    class Meta:
        app_label = "organization"
        db_table = "organization_organization_exam"


class OrganizationPackage(BaseModel):

    organization = models.ForeignKey("Organization", on_delete=models.CASCADE, related_name="organization_packages")
    package = models.ForeignKey("lookups.Package", on_delete=models.CASCADE)
    users = models.PositiveIntegerField(default=0)
    questions = models.PositiveIntegerField(default=0)
    exams = models.PositiveIntegerField(default=0)
    prep_exams = models.PositiveIntegerField(default=0)
    exam_attempts = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = "organization"
        db_table = "organization_organization_package"
