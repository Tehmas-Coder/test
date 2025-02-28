from cryptography.fernet import Fernet
from decouple import config

from helpers.email_notifications import EmailNotification
from helpers.helper_functions import get_encryption_key


class ExamScoringNinja:
    """
    This class is used to send the exam result to the candidate via Email.

    :Attributes:
    - `candidate_exam_id` (int): The candidate exam id.
    - `candidate_exam_instance` (CandidateExam): The candidate exam instance.

    :Methods:
    - `send_result_email_to_candidate()`: Sends the exam result to the candidate.
    """

    def __init__(self, candidate_exam_id=None, candidate_exam_instance=None) -> None:
        self.candidate_exam_id = candidate_exam_id
        self.candidate_exam_instance = candidate_exam_instance

    def send_result_email_to_candidate(self):
        candidate_first_name = self.candidate_exam_instance.candidate.user.first_name  # type: ignore
        candidate_last_name = self.candidate_exam_instance.candidate.user.last_name  # type: ignore
        candidate_email = self.candidate_exam_instance.candidate_email  # type: ignore
        exam = self.candidate_exam_instance.exam_backlog.name  # type: ignore

        key = get_encryption_key()
        cipher = Fernet(key)
        candidate_exam_id = self.candidate_exam_instance.id  # type: ignore
        encrypted_data = cipher.encrypt(str(candidate_exam_id).encode())
        token_data = encrypted_data.decode("utf-8")
        token = f"{token_data}"
        url = config("QB_PUBLIC_FE_URL")
        final_url = f"{url}/result/token={token}"

        send_email_data_dict = {
            "first_name": candidate_first_name,
            "last_name": candidate_last_name,
            "email": candidate_email,
            "exam": exam,
            "url": final_url,
        }

        email_notification_ninja = EmailNotification(send_email_data_dict)
        if not email_notification_ninja.send_exam_result():
            del email_notification_ninja
            return False
        del email_notification_ninja
        return True
