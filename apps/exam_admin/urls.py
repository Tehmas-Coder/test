from django.urls import include, path
from rest_framework import routers

from apps.exam_admin.views.exam_admin_views import (
    ExamSubjectQuestionViewSet,
    ExamSubjectViewSet,
    ExamViewSet,
    ScheduleViewSet,
    SectionViewSet,
    SubSectionViewSet,
)

router = routers.DefaultRouter()

router.register(r"sections", SectionViewSet)
router.register(r"subsections", SubSectionViewSet)
router.register(r"schedules", ScheduleViewSet)

router.register(r"exams", ExamViewSet)
router.register(r"exam-subject", ExamSubjectViewSet)
router.register(r"exam-subject-question", ExamSubjectQuestionViewSet)


urlpatterns = [
    path("", include(router.urls)),
]


urlpatterns += router.urls
