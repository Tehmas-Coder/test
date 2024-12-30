import mimetypes
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3
from botocore.exceptions import ClientError
from decouple import config
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django_q.tasks import async_task

from apps.emails.models.emails_models import EmailLog, EmailLogAttachment
from utils.rna_utils import color_print


def email_send_hook(task, *args, **kwargs):
    try:
        color_print(
            f"email_send_hook called. task.result: {task.result}",
            "blue",
        )

        # Check if result is a dictionary
        if not isinstance(task.result, dict):
            color_print(f"Unexpected task result: {task.result}", "red")
            return

        email_log_id = task.result.get("email_log_id")
        if email_log_id is None:
            color_print("No email_log_id found in task.result.", "red")
            return

        # Fetch the email log
        email_log = EmailLog.objects.get(id=email_log_id)

        # Update status based on task result
        if task.result.get("status") == "sent":
            email_log.status = "sent"
            color_print(f"Email sent successfully, Log ID: {email_log_id}", "green")
        else:
            email_log.status = "failed"
            email_log.error = task.result.get("error")
            color_print(f"Email sending failed, Log ID: {email_log_id}", "red")

        email_log.save()

    except Exception as e:
        color_print(f"Exception in email_send_hook: {e}", "red")
        raise


def send_email_task(
    subject: str,
    html_content: str,
    attachments: list = [],
    from_email: str = str(config("SYSTEM_EMAIL")),
    to_email_list: list[str] | None = None,
    cc_list: list[str] | None = None,
    bcc_list: list[str] | None = None,
):
    """
    This function logs the email to be sent and queues the email sending process asynchronously.
    Saves attachments to the database (and S3) and passes only the email log ID to the task.
    """

    # Create Email log
    email_log = EmailLog.objects.create(
        to_email_list=",".join(to_email_list) if to_email_list else None,
        from_email=from_email,
        subject=subject,
        body=html_content,
        status="queued",
        cc_list=",".join(cc_list) if cc_list else None,
        bcc_list=",".join(bcc_list) if bcc_list else None,
    )

    # Save attachments to the database and S3 via FileField
    for attachment in attachments:
        if isinstance(attachment, dict):
            color_print(f"Processing dict attachment: {attachment['filename']}", color="blue")
            # For dictionary-style attachments, save the file to S3 and database
            EmailLogAttachment.objects.create(
                email_log=email_log,
                name=attachment["filename"],
                ext=attachment["filename"].split(".")[-1],
                file=ContentFile(attachment["content"], name=attachment["filename"]),
            )
        elif isinstance(attachment, InMemoryUploadedFile):
            color_print(
                f"Processing InMemoryUploadedFile attachment: {attachment.name}",
                color="blue",
            )
            # Save InMemoryUploadedFile to the database and S3
            EmailLogAttachment.objects.create(
                email_log=email_log,
                name=attachment.name,
                ext=attachment.name.split(".")[-1],
                file=attachment,  # File is automatically uploaded to S3 via FileField
            )

    # Queue the email sending task asynchronously
    try:
        color_print(f"Queuing email sending task for log ID: {email_log.id}", color="yellow")  # type: ignore
        async_task(
            send_email_with_attachment_task,
            email_log_id=email_log.id,  # type: ignore
            hook="apps.emails.views.emails_views.email_send_hook",
        )
    except Exception as e:
        email_log.status = "failed"
        email_log.error = str(e)
        email_log.save()
        raise e


def send_email_with_attachment_task(email_log_id: int):
    """
    Fetches the email log and its attachments from the database and sends the email with attachments.
    Attachments are fetched from S3.
    """

    ses_client = boto3.client("ses")

    try:
        # Fetch the email log
        email_log = EmailLog.objects.get(id=email_log_id)
        color_print(f"Sending email for log ID: {email_log_id}", color="yellow")

        # Create the email message
        message = MIMEMultipart()
        message["From"] = email_log.from_email
        message["To"] = email_log.to_email_list
        message["Subject"] = email_log.subject

        if email_log.cc_list:
            message["Cc"] = email_log.get_cc_recipients()  # type: ignore

        # Attach the HTML body
        message.attach(MIMEText(email_log.body, "html"))

        # Fetch attachments from the database and attach them to the email
        for attachment in email_log.attachments.all():  # type: ignore
            # Open the file from S3 (using Django's file storage system)
            file = attachment.file.open(mode="rb")
            file_content = file.read()
            file_name = attachment.name
            mime_type, _ = mimetypes.guess_type(file_name)  # type: ignore
            mime_type = mime_type or "application/octet-stream"
            file.close()  # Close the file after reading

            # Attach the file to the email
            maintype, subtype = mime_type.split("/", 1)
            part = MIMEBase(maintype, subtype)
            part.set_payload(file_content)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={file_name}")
            color_print(f"Attaching file: {file_name}", color="blue")
            message.attach(part)

        # Send the email through SES
        response = ses_client.send_raw_email(
            Source=email_log.from_email,
            Destinations=email_log.get_recipients(),
            RawMessage={"Data": message.as_string()},
        )
        color_print(f"Email sent! Message ID: {response['MessageId']}", color="green")

        # Log success
        email_log.status = "sent"
        email_log.save()

        return {
            "email_log_id": email_log_id,
            "status": "sent",
            "message_id": response["MessageId"],
        }

    except ClientError as e:
        # Log failure
        email_log.status = "failed"
        email_log.error = str(e)
        email_log.save()

        color_print(f"Error sending email: {e}", color="red")
        raise e  # Re-raise the exception for retry handling

    except EmailLog.DoesNotExist:
        color_print(f"Email log with ID {email_log_id} does not exist.", color="red")
        # Return result indicating failure
        return {
            "email_log_id": email_log_id,
            "status": "failed",
            "error": "EmailLog.DoesNotExist",
        }
