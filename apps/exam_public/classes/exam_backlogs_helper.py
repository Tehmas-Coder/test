from django.db.models import F
from django.forms import model_to_dict

from apps.exam_public.models.exam_public_backlog_models import (
    ExamBacklogQuestion,
    ExamBacklogQuestionChoice,
    ExamBacklogQuestionCountry,
    SectionBacklog,
    SubSectionBacklog,
)
from apps.exam_public.serializers.backlog_serializers.exam_backlog_serializers import (
    ExamBacklogEditSerializer,
)
from utils.rna_utils import debug_print


class ExamBacklogs:
    def __init__(self, exam_data: dict) -> None:
        self.exam_data = exam_data
        self.section_backlog_ids_hashmap = {}
        self.subsection_backlog_ids_hashmap = {}
        self.question_backlog_ids_hashmap = {}
        self.exam_backlog_id = None

    def create_backlogs(self):
        # * Fetching other data from Exam Data
        exam_data = self.exam_data
        exam_data.pop("exam_subjects")

        exam_sections = exam_data.pop("sections")
        exam_subsections = exam_data.pop("subsections")
        exam_questions = exam_data.pop("questions")

        # * Creating Exam Backlog
        education_level = exam_data.pop("education_level")
        exam_data["exam"] = exam_data.pop("id")
        exam_data["education_level"] = education_level["id"]
        exam_data["education_level_name"] = education_level["name"]

        serializer = ExamBacklogEditSerializer(data=exam_data)
        serializer.is_valid(raise_exception=True)
        self.exam_backlog_id = serializer.save().id

        # * Creating other Exam Related Backlogs
        self.create_sections_backlogs(exam_sections)
        self.create_subsections_backlogs(exam_subsections)
        self.create_questions_backlogs(exam_questions)

    def create_sections_backlogs(self, exam_section_list):
        bulk_create_section_backlog_instances_list = []
        for section_dict in exam_section_list:
            # * Creating Sections Backlogs
            section_id = section_dict.pop("id")
            measuring_unit_id = section_dict.pop("measuring_unit")
            bulk_create_section_backlog_instances_list.append(
                SectionBacklog(section_id=section_id, measuring_unit_id=measuring_unit_id, exam_backlog_id=self.exam_backlog_id, **section_dict)
            )

        # * Bulk creating the sections Backlog
        SectionBacklog.objects.bulk_create(bulk_create_section_backlog_instances_list)
        created_section_backlog_queryset = (
            SectionBacklog.objects.annotate(sec_id=F("section__id")).all().order_by("-created_at")[: len(bulk_create_section_backlog_instances_list)]
        )
        created_section_backlog_instance_list = sorted(created_section_backlog_queryset, key=lambda instance: instance.id)

        # * Creating a hashmap which has section_ids as keys and section_backlog_ids as values
        for one_section_backlog in created_section_backlog_instance_list:
            section_id = one_section_backlog.sec_id
            section_backlog_id = one_section_backlog.id
            if not section_id in self.section_backlog_ids_hashmap:
                self.section_backlog_ids_hashmap[section_id] = section_backlog_id

    def create_subsections_backlogs(self, exam_subsection_list):
        bulk_create_subsection_backlog_instances_list = []
        for subsection_dict in exam_subsection_list:
            # * Creating SubSections Backlogs
            subsection_id = subsection_dict.pop("id")
            section_id = self.section_backlog_ids_hashmap[subsection_dict.pop("section")]
            measuring_unit_id = subsection_dict.pop("measuring_unit")
            bulk_create_subsection_backlog_instances_list.append(
                SubSectionBacklog(
                    section_id=section_id,
                    subsection_id=subsection_id,
                    measuring_unit_id=measuring_unit_id,
                    exam_backlog_id=self.exam_backlog_id,
                    **subsection_dict,
                )
            )

        # * Bulk creating the subsections Backlog
        SubSectionBacklog.objects.bulk_create(bulk_create_subsection_backlog_instances_list)
        created_subsection_backlog_queryset = (
            SubSectionBacklog.objects.annotate(subsec_id=F("subsection__id"))
            .all()
            .order_by("-created_at")[: len(bulk_create_subsection_backlog_instances_list)]
        )
        created_subsection_backlog_instance_list = sorted(created_subsection_backlog_queryset, key=lambda instance: instance.id)

        # * Creating a hashmap which has subsection_ids as keys and subsection_backlog_ids as values
        for one_subsection_backlog in created_subsection_backlog_instance_list:
            subsection_id = one_subsection_backlog.subsec_id
            subsection_backlog_id = one_subsection_backlog.id
            if not subsection_id in self.subsection_backlog_ids_hashmap:
                self.subsection_backlog_ids_hashmap[subsection_id] = subsection_backlog_id

    def create_questions_backlogs(self, exam_question_list):
        question_bulk_create_list = []
        for one_exam_question in exam_question_list:
            question_data = one_exam_question["question"]
            question_bulk_create_list.append(
                ExamBacklogQuestion(
                    exam_backlog_id=self.exam_backlog_id,
                    subject_id=one_exam_question["subject"]["id"],
                    subject_name=one_exam_question["subject"]["name"],
                    education_level_id=one_exam_question["education_level"]["id"],
                    education_level_name=one_exam_question["education_level"]["name"],
                    question_id=question_data["id"],
                    type_id=question_data["type"]["id"],
                    title=question_data["title"],
                    text=question_data["text"],
                    max_retries=question_data["max_retries"],
                    retry_penalty=question_data["retry_penalty"],
                    can_shuffle=question_data["can_shuffle"],
                    has_media=question_data["has_media"],
                    time_limit=question_data["time_limit"],
                    total_marks=question_data["total_marks"],
                    is_optional=question_data["is_optional"],
                    is_global=question_data["is_global"],
                    difficulty_id=question_data["difficulty_level"]["id"],
                    difficulty_name=question_data["difficulty_level"]["name"],
                    measuring_unit_id=question_data["measuring_unit"]["id"],
                    measuring_unit_name=question_data["measuring_unit"]["name"],
                    sequence=one_exam_question["sequence"],
                    description=one_exam_question["description"],
                    section_id=int(self.section_backlog_ids_hashmap[one_exam_question["section"]]) if one_exam_question["section"] else None,
                    subsection_id=(
                        int(self.subsection_backlog_ids_hashmap[one_exam_question["subsection"]]) if one_exam_question["subsection"] else None
                    ),
                )
            )
        # * Bulk Create Questions
        if len(question_bulk_create_list):
            ExamBacklogQuestion.objects.bulk_create(question_bulk_create_list)

        created_question_backlog_queryset = (
            ExamBacklogQuestion.objects.annotate(
                ques_id=F("question__id"),
            )
            .all()
            .order_by("-created_at")[: len(question_bulk_create_list)]
        )
        created_question_backlog_instance_list = sorted(created_question_backlog_queryset, key=lambda instance: instance.id)

        self.question_country_bulk_create_list = []
        self.question_choices_bulk_create_list = []
        for index, one_exam_question in enumerate(exam_question_list):
            exam_question_backlog_id: int = created_question_backlog_instance_list[index].id
            exam_question_countries: list = one_exam_question["question"]["countries"]
            exam_question_choices: list = one_exam_question["question"]["choices"]

            if len(exam_question_countries):
                self.create_question_country_backlogs(exam_question_backlog_id, exam_question_countries)

            if len(exam_question_choices):
                self.create_question_choices_backlogs(exam_question_backlog_id, exam_question_choices)

        # * Bulk Create Questions all Related data
        if len(self.question_country_bulk_create_list):
            ExamBacklogQuestionCountry.objects.bulk_create(self.question_country_bulk_create_list)

        if len(self.question_choices_bulk_create_list):
            ExamBacklogQuestionChoice.objects.bulk_create(self.question_choices_bulk_create_list)

    def create_question_country_backlogs(self, exam_question_backlog_id, exam_question_countries):
        for one_dict in exam_question_countries:
            self.question_country_bulk_create_list.append(
                ExamBacklogQuestionCountry(
                    exam_question_backlog_id=exam_question_backlog_id,
                    country_id=one_dict["id"],
                )
            )

    def create_question_choices_backlogs(self, exam_question_backlog_id, exam_question_choices):
        for one_dict in exam_question_choices:
            self.question_choices_bulk_create_list.append(
                ExamBacklogQuestionChoice(
                    exam_question_backlog_id=exam_question_backlog_id,
                    question_choice_id=one_dict["id"],
                    name="TEST",
                    title=one_dict["title"],
                    text=one_dict["text"],
                    weight=one_dict["weight"],
                    is_negative_weight=one_dict["is_negative_weight"],
                    is_correct=one_dict["is_correct"],
                    has_media=one_dict["has_media"],
                )
            )
