from botocore.exceptions import ClientError
from django.core.mail import send_mail
from decouple import config
import boto3
import json


def send_email(subject, html_content, email, use_queue=True):
    to_email_list = [email]
    from_email = config("SYSTEM_EMAIL")
    email_body = ""

    return send_email_notification_to_list(
        subject, email_body, html_content, to_email_list, from_email, use_queue  # type: ignore
    )


def send_email_notification_to_list(
    subject: str,
    email_body: str,
    email_body_html,
    to_email_list: list[str],
    from_email: str = "haiderjuttearner@gmail.com",
    queue: bool = False,
):
    if not queue:
        return send_mail(subject, email_body, from_email, to_email_list)
    else:
        res = add_to_email_queue(
            message={
                "subject": subject,
                "email_body_html": email_body_html,
                "email_body": email_body,
                "from_email": from_email,
                "to_email_list": to_email_list,
            }
        )
        return 1 if res == 200 else 0


def add_to_email_queue(message: dict):
    sqs_client = boto3.client("sqs")
    if config("MOCK_SEND_EMAIL") == "1":
        return 200
    else:
        try:
            response = sqs_client.send_message(
                QueueUrl=config("EMAIL_QUEUE_NAME"), MessageBody=json.dumps(message)
            )
            return response["ResponseMetadata"]["HTTPStatusCode"]
        except ClientError as error:
            print(error)
            return error


def send_verification_link_or_otp_to_email(
    send_email_data_dict, send_otp=False, send_url=False, subject="Email Verification"
):
    first_name = send_email_data_dict["first_name"]
    last_name = send_email_data_dict["last_name"]
    user_email = send_email_data_dict["email"]

    if send_otp:
        otp = send_email_data_dict["otp"]
        with open("templates/email/otp_email.html", "r", encoding="utf-8") as file:
            html_content = (
                file.read()
                .replace("{FIRST_NAME}", first_name)
                .replace("{LAST_NAME}", last_name)
                .replace("{EMAIL}", user_email)
                .replace("{OTP}", otp)
            )

    return send_email(subject, html_content, user_email)
