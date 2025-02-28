from hooks.webhooks import GenericWebhook


def send_exam_result_to_student_apply_webhook(candidate_exam_instance):
    """
    This function is used to send the exam result to the candidate via webhook.

    Args:
    - `candidate_exam_instance` (CandidateExam): The candidate exam instance.

    Returns:
    - bool: True if the webhook is sent successfully, False otherwise.
    """
    encryption_key = candidate_exam_instance.candidate.organization.encryption_key
    token = candidate_exam_instance.candidate.organization.token
    data = {
        "event_type": "exam_result",
        "data": {
            "candidate_exam_id": candidate_exam_instance.id,  # type: ignore
            "total_marks": candidate_exam_instance.total_obtainable_marks,
            "obtained_marks": candidate_exam_instance.obtained_marks,
            "exam_status": candidate_exam_instance.exam_status,
        },
    }
    webhook_instance = GenericWebhook(data_dict=data)
    return webhook_instance.send_request(encryption_key, token)
