from django.db.models import F
from django.forms import model_to_dict

from apps.exam_public.models.exam_public_backlog_models import (
    ExamBacklogQuestion,
    ExamBacklogQuestionAttemptResponse,
    ExamBacklogQuestionChoice,
    ExamBacklogQuestionChoiceMedia,
    ExamBacklogQuestionCountry,
    ExamBacklogQuestionMedia,
    ExamBacklogQuestionRetryHint,
    ExamBacklogQuestionRetryHintMedia,
    ExamBacklogQuestionTag,
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

        return self.exam_backlog_id

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
                    section_backlog_id=int(self.section_backlog_ids_hashmap[one_exam_question["section"]]) if one_exam_question["section"] else None,
                    subsection_backlog_id=(
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
        self.created_question_backlog_instance_list = sorted(created_question_backlog_queryset, key=lambda instance: instance.id)

        # * Intializing Bulk create lists for question related data
        """
        ->
        """
        self.question_medias_bulk_create_list = []
        self.question_country_bulk_create_list = []
        self.question_choices_bulk_create_list = []
        self.question_choices_medias_bulk_create_list = []
        self.question_tags_bulk_create_list = []
        self.question_retry_hints_bulk_create_list = []
        self.question_attempt_responses_bulk_create_list = []

        self.question_choices_hashmap = {}
        self.question_retry_hints_hashmap = {}
        for index, one_exam_question in enumerate(exam_question_list):
            self.question_choices_hashmap = {one_choice["id"]: one_choice for one_choice in one_exam_question["question"]["choices"]}
            self.question_retry_hints_hashmap = {
                one_retry_hints["id"]: one_retry_hints for one_retry_hints in one_exam_question["question"]["retry_hints"]
            }

            # * Fetching and setting up data from the question to pass it to the backlogs creation functions
            exam_backlog_question_id: int = self.created_question_backlog_instance_list[index].id
            exam_question_medias: list = one_exam_question["question"]["medias"]
            exam_question_countries: list = one_exam_question["question"]["countries"]
            exam_question_choices: list = one_exam_question["question"]["choices"]
            exam_question_tags: list = one_exam_question["question"]["tags"]
            exam_question_retry_hints: list = one_exam_question["question"]["retry_hints"]
            exam_question_attempt_responses: list = one_exam_question["question"]["attempt_responses"]

            # * Calling Backlogs creation functions to fetch bulk create list of question related data
            if len(exam_question_medias):
                self.create_question_medias_backlogs(exam_backlog_question_id, exam_question_medias)

            if len(exam_question_countries):
                self.create_question_country_backlogs(exam_backlog_question_id, exam_question_countries)

            if len(exam_question_choices):
                self.create_question_choices_backlogs(exam_backlog_question_id, exam_question_choices)

            if len(exam_question_tags):
                self.create_question_tags_backlogs(exam_backlog_question_id, exam_question_tags)

            if len(exam_question_retry_hints):
                self.create_question_retry_hints_backlogs(exam_backlog_question_id, exam_question_retry_hints)

            if len(exam_question_attempt_responses):
                self.create_question_attempt_responses_backlogs(exam_backlog_question_id, exam_question_attempt_responses)

        # * Bulk Create Questions all Related data
        if len(self.question_medias_bulk_create_list):
            ExamBacklogQuestionMedia.objects.bulk_create(self.question_medias_bulk_create_list)

        if len(self.question_country_bulk_create_list):
            ExamBacklogQuestionCountry.objects.bulk_create(self.question_country_bulk_create_list)

        if len(self.question_choices_bulk_create_list):
            ExamBacklogQuestionChoice.objects.bulk_create(self.question_choices_bulk_create_list)

        if len(self.question_tags_bulk_create_list):
            ExamBacklogQuestionTag.objects.bulk_create(self.question_tags_bulk_create_list)

        if len(self.question_retry_hints_bulk_create_list):
            ExamBacklogQuestionRetryHint.objects.bulk_create(self.question_retry_hints_bulk_create_list)

        if len(self.question_attempt_responses_bulk_create_list):
            ExamBacklogQuestionAttemptResponse.objects.bulk_create(self.question_attempt_responses_bulk_create_list)

        self.media_backlog_creation(exam_question_list)

    def create_question_medias_backlogs(self, exam_backlog_question_id, exam_question_medias):
        for one_dict in exam_question_medias:
            self.question_medias_bulk_create_list.append(
                ExamBacklogQuestionMedia(
                    exam_backlog_question_id=exam_backlog_question_id,
                    media_id=one_dict["media"]["id"],
                )
            )

    def create_question_country_backlogs(self, exam_backlog_question_id, exam_question_countries):
        for one_dict in exam_question_countries:
            self.question_country_bulk_create_list.append(
                ExamBacklogQuestionCountry(
                    exam_backlog_question_id=exam_backlog_question_id,
                    country_id=one_dict["id"],
                )
            )

    def create_question_choices_backlogs(self, exam_backlog_question_id, exam_question_choices):
        for one_dict in exam_question_choices:
            self.question_choices_bulk_create_list.append(
                ExamBacklogQuestionChoice(
                    exam_backlog_question_id=exam_backlog_question_id,
                    question_choice_id=one_dict["id"],
                    title=one_dict["title"],
                    text=one_dict["text"],
                    weight=one_dict["weight"],
                    is_negative_weight=one_dict["is_negative_weight"],
                    is_correct=one_dict["is_correct"],
                    has_media=one_dict["has_media"],
                )
            )

    def create_question_tags_backlogs(self, exam_backlog_question_id, exam_question_tags):
        for one_dict in exam_question_tags:
            self.question_tags_bulk_create_list.append(
                ExamBacklogQuestionTag(
                    exam_backlog_question_id=exam_backlog_question_id,
                    tag_id=one_dict["id"],
                    name=one_dict["name"],
                )
            )

    def create_question_retry_hints_backlogs(self, exam_backlog_question_id, exam_question_retry_hints):
        for one_dict in exam_question_retry_hints:
            self.question_retry_hints_bulk_create_list.append(
                ExamBacklogQuestionRetryHint(
                    exam_backlog_question_id=exam_backlog_question_id,
                    retry_hint_id=one_dict["id"],
                    text=one_dict["text"],
                    sequence=one_dict["sequence"],
                    has_media=one_dict["has_media"],
                )
            )

    def create_question_attempt_responses_backlogs(self, exam_backlog_question_id, exam_question_attempt_responses):
        for one_dict in exam_question_attempt_responses:
            self.question_attempt_responses_bulk_create_list.append(
                ExamBacklogQuestionAttemptResponse(
                    exam_backlog_question_id=exam_backlog_question_id,
                    attempt_response_id=one_dict["id"],
                    text=one_dict["text"],
                    type=one_dict["type"],
                )
            )

    def media_backlog_creation(self, exam_question_list):
        newly_created_choices_backlog_queryset = ExamBacklogQuestionChoice.objects.all().order_by("-created_at")[
            : len(self.question_choices_bulk_create_list)
        ]
        newly_created_choices_backlog_instance_list = sorted(newly_created_choices_backlog_queryset, key=lambda instance: instance.id)

        newly_created_retry_hints_backlog_queryset = ExamBacklogQuestionRetryHint.objects.all().order_by("-created_at")[
            : len(self.question_retry_hints_bulk_create_list)
        ]
        newly_created_retry_hints_backlog_instance_list = sorted(newly_created_retry_hints_backlog_queryset, key=lambda instance: instance.id)

        # QUESTION CHOICE MEDIA BACKLOG
        self.question_choices_medias_bulk_create_list = []
        for one_question_choice_backlog in newly_created_choices_backlog_instance_list:
            from_backlog_question_choice_id = one_question_choice_backlog.question_choice_id
            question_choice_data = self.question_choices_hashmap[from_backlog_question_choice_id]
            one_question_choice_backlog_id = one_question_choice_backlog.id
            choices_media_list = question_choice_data["medias"]
            if len(choices_media_list):
                for one_dict in choices_media_list:
                    self.question_choices_medias_bulk_create_list.append(
                        ExamBacklogQuestionChoiceMedia(
                            exam_backlog_question_choice_id=one_question_choice_backlog_id,
                            media_id=one_dict["media"]["id"],
                        )
                    )

        if len(self.question_choices_medias_bulk_create_list):
            ExamBacklogQuestionChoiceMedia.objects.bulk_create(self.question_choices_medias_bulk_create_list)

        # QUESTION RETRY HINTS MEDIA BACKLOG
        self.question_retry_hints_medias_bulk_create_list = []
        for one_question_retry_hint_backlog in newly_created_retry_hints_backlog_instance_list:
            from_backlog_question_retry_hint_id = one_question_retry_hint_backlog.retry_hint_id

            question_retry_hint_data = self.question_retry_hints_hashmap[from_backlog_question_retry_hint_id]
            one_question_retry_hint_backlog_id = one_question_retry_hint_backlog.id
            retry_hints_media_list = question_retry_hint_data["medias"]
            if len(retry_hints_media_list):
                for one_dict in retry_hints_media_list:
                    self.question_retry_hints_medias_bulk_create_list.append(
                        ExamBacklogQuestionRetryHintMedia(
                            exam_backlog_question_retry_hint_id=one_question_retry_hint_backlog_id,
                            media_id=one_dict["media"]["id"],
                        )
                    )

        if len(self.question_retry_hints_medias_bulk_create_list):
            ExamBacklogQuestionRetryHintMedia.objects.bulk_create(self.question_retry_hints_medias_bulk_create_list)
