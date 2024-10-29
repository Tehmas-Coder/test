from webhooks.generic_webhook import GenericWebhook


def send_exam_result_to_student_apply_webhook(candidate_exam_instance):
    encryption_key = candidate_exam_instance.candidate.organization.encryption_key
    token = candidate_exam_instance.candidate.organization.token
    data = {
        "event_type": "exam_result",
        "exam_name": candidate_exam_instance.exam_backlog.name,
        "candidate_exam_id": candidate_exam_instance.id,  # type: ignore
        "total_marks": candidate_exam_instance.total_obtainable_marks,
        "obtained_marks": candidate_exam_instance.obtained_marks,
    }
    webhook_instance = GenericWebhook(data_dict=data)
    return webhook_instance.send_request(encryption_key, token)
