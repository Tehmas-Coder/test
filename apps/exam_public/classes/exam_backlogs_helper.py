from django.db.models import F
from django.forms import model_to_dict

from apps.exam_public.models.exam_public_backlog_models import (
    SectionBacklog,
    SubSectionBacklog,
)
from apps.exam_public.serializers.backlog_serializers.exam_backlog_serializers import (
    ExamBacklogEditSerializer,
)
from apps.exam_public.serializers.backlog_serializers.section_backlog_serializers import (
    SectionBacklogEditSerializer,
)
from apps.exam_public.serializers.backlog_serializers.subsection_backlog_serializers import (
    SubSectionBacklogEditSerializer,
)
from utils.rna_utils import debug_print


class ExamBacklogs:
    def __init__(self, exam_data: dict) -> None:
        self.exam_data = exam_data

    def create_backlogs(self):
        # * Fetching other data from Exam Data
        exam_data = self.exam_data
        exam_data.pop("exam_subjects")

        exam_questions = exam_data.pop("questions")
        exam_sections = exam_data.pop("sections")
        exam_subsections = exam_data.pop("subsections")

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
        # self.create_subsections_backlogs(exam_subsections)

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
            SectionBacklog.objects.annotate(sec_id=F("section__id")).all().order_by("-id")[: len(bulk_create_section_backlog_instances_list)]
        )
        created_section_backlog_instance_list = sorted(created_section_backlog_queryset, key=lambda instance: instance.id)

        # * Creating a hashmap which has section_ids as keys and section_backlog_ids as values
        self.section_backlog_ids_hashmap = {}
        for one_section_backlog in created_section_backlog_instance_list:
            section_id = one_section_backlog.sec_id
            section_backlog_id = one_section_backlog.id
            if not section_id in self.section_backlog_ids_hashmap:
                self.section_backlog_ids_hashmap[section_id] = section_backlog_id

    def create_subsections_backlogs(self, subsections_list):
        bulk_create_subsection_backlog_instances_list = []
        for subsection_dict in subsections_list:
            # * Creating SubSections Backlogs
            subsection_id = subsection_dict.pop("id")
            measuring_unit_id = subsection_dict.pop("measuring_unit")
            bulk_create_subsection_backlog_instances_list.append(
                SubSectionBacklog(
                    subsection_id=subsection_id, measuring_unit_id=measuring_unit_id, exam_backlog_id=self.exam_backlog_id, **subsection_dict
                )
            )

        # * Bulk creating the subsections Backlog
        SubSectionBacklog.objects.bulk_create(bulk_create_subsection_backlog_instances_list)
        created_section_backlog_queryset = (
            SubSectionBacklog.objects.annotate(sec_id=F("section__id")).all().order_by("-id")[: len(bulk_create_subsection_backlog_instances_list)]
        )
        created_section_backlog_instance_list = sorted(created_section_backlog_queryset, key=lambda instance: instance.id)

        # * Creating a hashmap which has subsection_ids as keys and section_backlog_ids as values
        self.section_backlog_ids_hashmap = {}
        for one_section_backlog in created_section_backlog_instance_list:
            subsection_id = one_section_backlog.sec_id
            section_backlog_id = one_section_backlog.id
            if not subsection_id in self.section_backlog_ids_hashmap:
                self.section_backlog_ids_hashmap[subsection_id] = section_backlog_id
