from django.db.models import Prefetch, Q


def get_exam_detailed_queryset(
    model, sections=False, exam_subject=False, exam_subject_questions=False, exam_subject_questions_question=False, all=False
):
    from apps.exam_admin.models.exam_admin_models import ExamSubject

    exam_queryset = model.objects.all().select_related("education_level")

    if sections or all:
        from apps.exam_admin.models.exam_admin_models import Section

        exam_queryset = exam_queryset.prefetch_related(
            Prefetch(
                "sections",
                Section.objects.filter(meta_status="active").prefetch_related(
                    "subsections",
                ),
            )
        )
    if exam_subject or all:
        exam_queryset = exam_queryset.prefetch_related(
            Prefetch(
                "examsubject_set",
                queryset=ExamSubject.objects.all().select_related(
                    "subject_education_level",
                    "subject_education_level__subject",
                    "subject_education_level__education_level",
                ),
            )
        )
    if exam_subject_questions or all:
        from apps.exam_admin.models.exam_admin_models import ExamSubjectQuestion

        exam_queryset = exam_queryset.prefetch_related(
            Prefetch(
                "examsubject_set__examsubjectquestion_set",
                queryset=ExamSubjectQuestion.objects.filter(
                    Q(
                        Q(section__isnull=True)
                        | Q(subsection__isnull=True)
                        | Q(
                            section__isnull=False,
                            section__meta_status="active",
                        )
                        | Q(
                            subsection__isnull=False,
                            subsection__meta_status="active",
                        )
                    )
                ).select_related("section", "subsection"),
            )
        )
    if exam_subject_questions_question or all:
        from apps.questionbank.models import Question

        exam_queryset = exam_queryset.prefetch_related(
            Prefetch(
                "examsubject_set__examsubjectquestion_set__question",
                queryset=Question.get_detail_queryset(all=True),
            )
        )
    return exam_queryset
