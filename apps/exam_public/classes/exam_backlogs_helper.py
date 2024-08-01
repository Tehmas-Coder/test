from django.forms import model_to_dict

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
        debug_print(self.exam_data)
        # for one_candidate_dict in self.candidate_exam_list:
        #     self.candidate_exam_id = one_candidate_dict["id"]
        #     exam_data = one_candidate_dict["exam"]
        #     exam_sections_data = exam_data["sections"]
        #     exam_subject_data = exam_data["exam_subjects"]
        #     exam_questions_data = exam_data["questions"]

        # self.create_questions_backlog(exam_questions_data)
        # self.create_sections_backlogs(exam_sections_data)
        return

    def create_questions_backlog(self, question_list):
        for one_question in question_list:
            debug_print(one_question, "yellow")
            return

    def create_sections_backlogs(self, exam_section_list):
        for one_section_dict in exam_section_list:
            # * Creating Section Backlog
            section_data = one_section_dict["section"]
            section_data["section"] = section_data.pop("id")
            section_data["candidate_exam"] = self.candidate_exam_id
            section_backlog_serializer = SectionBacklogEditSerializer(data=section_data)
            section_backlog_serializer.is_valid(raise_exception=True)
            section_backlog_serializer.save()
            section_backlog_id = section_backlog_serializer.data["id"]

            # * Creating subsections backlogs if subsections of a section exists
            if one_section_dict["subsections"]:
                subsections_list = one_section_dict["subsections"]
                for one_subsection_dict in subsections_list:
                    subsection_data = one_subsection_dict["subsection"]
                    subsection_data["subsection"] = subsection_data.pop("id")
                    subsection_data["section"] = section_backlog_id
                    subsection_data["candidate_exam"] = self.candidate_exam_id
                    subsection_backlog_serializer = SubSectionBacklogEditSerializer(data=subsection_data)
                    subsection_backlog_serializer.is_valid(raise_exception=True)
                    subsection_backlog_serializer.save()
                    subsection_backlog_id = subsection_backlog_serializer.data["id"]  # type: ignore
