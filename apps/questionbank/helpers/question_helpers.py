from apps.questionbank.models.question_models import Question, SubjectEducationLevel
from apps.questionbank.serializers.media_serializers import MediaSerializer
from middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import make_error_response


# ---------------------------------------------------------------------------- #
#                     QUESTIONBANK LOOKUPS HELPER FUNCTIONS                    #
# ---------------------------------------------------------------------------- #
def check_subject_education_level_existence(subject_id: int, education_level_id: int, instance_id: int | None = None) -> None:
    """
    This function is used to check if the subject education level exists.
    """
    if SubjectEducationLevel.objects.filter(subject_id=subject_id, education_level_id=education_level_id).exclude(id=instance_id).exists():
        ResponseMiddleware.return_now(make_error_response(message="Failed: This subject education level already exists."))


# ---------------------------------------------------------------------------- #
#                    QUESTION CREATION API HELPER FUNCTIONS                    #
# ---------------------------------------------------------------------------- #
def bulk_create_question_choices_or_retry_hints(question_instance: Question, data: list, model) -> None:
    """
    This function is used to bulk create question choices or retry hints for question.
    """
    for item in data:
        medias = item.pop("medias", [])
        item["question"] = question_instance
        instance = model.objects.create(**item)
        bulk_create_media_instances(medias, instance)


def bulk_create_media_instances(medias: list, instance) -> None:
    """
    This function is used to bulk create media instances for question, question choices or retry hints.
    """
    for item in medias:
        media_instance = MediaSerializer().create(item)
        instance.medias.add(media_instance)


def question_title_p_tag_stripper(question_title: str) -> str:
    """
    This function is used to strip the p tag from the question title start and end.
    """
    if question_title.startswith("<p>") and question_title.endswith("</p>"):
        question_title = question_title[3:-4]
    return question_title
