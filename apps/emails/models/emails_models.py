from django.db import models

from core.models import BaseModel


class EmailLog(BaseModel):
    """
    Model for logging email activity.

    - id: Autofield (PK)
    - to_email_list: TextField
    - from_email: EmailField
    - subject: CharField
    - body: TextField
    - sent_at: DateTimeField
    - status: CharField
        Choices:
            - "queued"
            - "sent"
            - "failed"
    - error: TextField
    - cc_list: EmailField
    - bcc_list: EmailField
    """

    to_email_list = models.TextField()  # Store as comma-separated values
    from_email = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=50,
        choices=[("queued", "Queued"), ("sent", "Sent"), ("failed", "Failed")],
        default="queued",
    )
    error = models.TextField(blank=True, null=True)
    cc_list = models.EmailField(blank=True, null=True)  # Store as comma-separated values
    bcc_list = models.EmailField(blank=True, null=True)  # Store as comma-separated values

    def __str__(self):
        return f"Email Log: {self.subject} to {self.get_cc_recipients()}"

    def get_recipients(self):
        """Return a list of recipients from the to_email_list."""
        return self.to_email_list.split(",") if self.to_email_list else []

    def get_cc_recipients(self):
        """Return a list of CC recipients from the cc_list."""
        return self.cc_list.split(",") if self.cc_list else []

    def get_bcc_recipients(self):
        """Return a list of BCC recipients from the bcc_list."""
        return self.bcc_list.split(",") if self.bcc_list else []

    class Meta:
        app_label = "emails"
        db_table = "emails_emaillog"


class EmailLogAttachment(BaseModel):
    """
    Model for logging email attachments.

    - id: Autofield (PK)
    - email_log: EmailLog (FK)
    - file: FileField
    - name: CharField
    - ext: CharField
    - uploaded_at: DateTimeField
    """

    email_log = models.ForeignKey(EmailLog, related_name="attachments", on_delete=models.CASCADE)
    file = models.FileField(upload_to="email_attachments/")
    name = models.CharField(max_length=255)
    ext = models.CharField(max_length=10)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.email_log.subject}"

    class Meta:
        app_label = "emails"
        db_table = "emails_emaillog_attachment"
