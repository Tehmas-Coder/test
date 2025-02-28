from hooks.webhooks import GenericWebhook


def send_exam_status_to_student_apply_webhook(candidate_exam_instance):
    """
    This function is used to send the exam status to the candidate via webhook.

    Args:
    - `candidate_exam_instance` (CandidateExam): The candidate exam instance.

    Returns:
    - bool: True if the webhook is sent successfully, False otherwise.
    """
    encryption_key = candidate_exam_instance.candidate.organization.encryption_key
    token = candidate_exam_instance.candidate.organization.token
    data = {
        "event_type": "exam_status",
        "data": {
            "candidate_exam_id": candidate_exam_instance.id,  # type: ignore
            "exam_status": candidate_exam_instance.exam_status,
        },
    }
    webhook_instance = GenericWebhook(data_dict=data)
    return webhook_instance.send_request(encryption_key, token)
