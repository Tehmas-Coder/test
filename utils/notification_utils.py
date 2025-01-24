import json
from doctest import debug
from email import encoders
from email.mime.base import MIMEBase

# * FOR Attachments
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3
from botocore.exceptions import ClientError
from decouple import config
from django.core.mail import send_mail

from apps.emails.views.emails_views import send_email_task
from utils.rna_utils import debug_print

# ------------------------------------------------------
# *                  SMS Utils
# ------------------------------------------------------


def send_sms_notification_to_number(
    message: str,
    phone_number: str,
    queue: bool = False,
):
    if not queue:
        return send_sms(message, phone_number)
    else:
        res = add_to_sms_queue(message={"message_text": message, "phone_number": phone_number})
        return 1 if res == 200 else 0


def send_sms(
    message: str,
    phone_number: str,
):
    # mock sms
    if config("MOCK_SEND_SMS") == "1":
        print("MOCKED SMS")
        return 1

    # sending sms
    try:
        sns_client = boto3.client("sns")
        response = sns_client.publish(PhoneNumber=phone_number, Message=message)
        print(response)
        return 1 if response["ResponseMetadata"]["HTTPStatusCode"] == 200 else 0
    except ClientError as error:
        print(error)
        return error


def add_to_sms_queue(message: dict):
    sqs_client = boto3.client("sqs")
    if config("MOCK_SEND_SMS") == "1":
        print("MOCKED SMS")
        return 200
    else:
        try:
            response = sqs_client.send_message(QueueUrl=config("SMS_QUEUE_NAME"), MessageBody=json.dumps(message))
            return response["ResponseMetadata"]["HTTPStatusCode"]
        except ClientError as error:
            print(error)
            return error


# ------------------------------------------------------
# *                  Email Utils
# ------------------------------------------------------


def send_email_notification_to_list(
    subject: str,
    email_body: str,
    email_body_html,
    to_email_list: list[str],
    from_email: str = "haiderjuttearner@gmail.com",
    queue: bool = False,
):
    if int(config("IS_DIVERT_EMAIL")):
        to_email_list = [str(config("DEFAULT_TO_EMAIL"))]
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
            response = sqs_client.send_message(QueueUrl=config("EMAIL_QUEUE_NAME"), MessageBody=json.dumps(message))
            return response["ResponseMetadata"]["HTTPStatusCode"]
        except ClientError as error:
            print(error)
            return error

    # if config("MOCK_SEND_EMAIL") == "1":
    #     return 200
    # else:
    #     result = send_email_task(
    #         subject=message["subject"],
    #         html_content=message["email_body_html"],
    #         from_email=message["from_email"],
    #         to_email_list=message["to_email_list"],
    #     )
    #     return 200 if type(result) == str else 400


def send_email_with_attachment(
    subject: str,
    email_body: str,
    email_body_html,
    to_email_list: list[str],
    from_email: str = "haiderjuttearner@gmail.com",
    file_name: str = "application.pdf",
    attachments=None,
):
    ses_client = boto3.client("ses")
    if config("MOCK_SEND_EMAIL") == "1":
        return 200
    else:
        try:
            message = MIMEMultipart()
            message["From"] = from_email
            message["To"] = ", ".join(to_email_list)
            message["Subject"] = subject

            message.attach(MIMEText(email_body_html, "html"))

            for attachment in attachments:  # type: ignore
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment)
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={file_name}")
                message.attach(part)

            response = ses_client.send_raw_email(
                Source=from_email,
                Destinations=to_email_list,
                RawMessage={"Data": message.as_string()},
            )
            # print("Email sent! Message ID:", response["MessageId"])

            res = response["ResponseMetadata"]["HTTPStatusCode"]
            return 1 if res == 200 else 0
        except ClientError as error:
            print(error.response["Error"]["Message"])
            return error
