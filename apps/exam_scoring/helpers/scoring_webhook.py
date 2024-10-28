# create a function to send exam name, cndidate exam id , total marks, obtained marks thorugh webhook
import requests


def send_exam_result_to_student_apply_webhook(candidate_exam_instance):
    exam_name = candidate_exam_instance.exam_backlog.name
    candidate_exam_id = candidate_exam_instance.id  # type: ignore
    total_marks = candidate_exam_instance.total_obtainable_marks
    obtained_marks = candidate_exam_instance.obtained_marks
    webhook_url = candidate_exam_instance.candidate.organization.webhook_url
    data = {
        "exam_name": exam_name,
        "candidate_exam_id": candidate_exam_id,
        "total_marks": total_marks,
        "obtained_marks": obtained_marks,
    }
    response = requests.post(webhook_url, json=data)
    return True if response.status_code == 200 else False
