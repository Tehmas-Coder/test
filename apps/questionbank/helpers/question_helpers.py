from apps.questionbank.models.question_models import SubjectEducationLevel
from middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import make_error_response


# ---------------------------------------------------------------------------- #
#                     QUESTIONBANK LOOKUPS HELPER FUNCTIONS                    #
# ---------------------------------------------------------------------------- #
def check_subject_education_level_existence(subject_id: int, education_level_id: int, instance_id=None):
    """
    This function is used to check if the subject education level exists.
    """
    if SubjectEducationLevel.objects.filter(subject_id=subject_id, education_level_id=education_level_id).exclude(id=instance_id).exists():
        ResponseMiddleware.return_now(make_error_response(message="Failed: This subject education level already exists."))
