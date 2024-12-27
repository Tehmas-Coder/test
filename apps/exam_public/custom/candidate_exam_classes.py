import json

from cryptography.fernet import Fernet

from apps.exam_public.helpers.candidate_exam_helpers import (
    get_detailed_candidate_exam_with_country_based_questions,
)
from apps.exam_public.models.exam_public_models import CandidateExam
from middlewares.current_user_middleware import get_current_user
from middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import get_encryption_key, make_error_response


class CandidateExamNinja:

    def __init__(self) -> None:
        pass

    def get_candidate_exam(self, candidate_exam_id):
        logged_in_user_id = get_current_user().id  # type:ignore

        try:
            candidate_exam_id = int(candidate_exam_id)
        except:
            try:
                token = candidate_exam_id[len("token=") :]
                key = get_encryption_key()
                cipher = Fernet(key)
                decrypted_data = json.loads(cipher.decrypt(token).decode())
                candidate_exam_id = decrypted_data["candidate_exam_id"]
            except:
                ResponseMiddleware.return_now(make_error_response(message="Invalid token"))

        # * IF ROLES ARE ( Organization Roles and Candidate )
        logged_in_user_roles = get_current_user().get_user_role_slugs  # type:ignore
        if len(logged_in_user_roles):
            if "candidate" in logged_in_user_roles:
                candidate_exam_filter_data = {
                    "id": candidate_exam_id,
                    "candidate__user__id": logged_in_user_id,
                }

                if not CandidateExam.objects.filter(**candidate_exam_filter_data).exists():
                    ResponseMiddleware.return_now(make_error_response(message="Exam not allowed to this candidate"))
        return get_detailed_candidate_exam_with_country_based_questions(candidate_exam_id)
