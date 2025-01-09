import io

from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.emails.views.emails_views import send_email_task
from apps.user.models.user_models import BaseUser
from utils.db_utils import create_seed_from_db


class TempApi(APIView):
    # def get(self, request):
    #     res = create_seed_from_db(BaseUser)
    #     return Response(res)

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # if request is not from localhost, return 404
        # TODO: Uncomment the following code block to restrict the API to localhost after testing on production is done
        # if request.META["REMOTE_ADDR"] not in ["localhost", "127.0.0.1"]:
        #     return Response(status=404)
        # for i in range(1, 3):
        #     send_email_task(
        #         subject=f"Test Email {i} from Django",
        #         html_content="<h1>This is a test email</h1>",
        #         from_email="haiderjuttearner@gmail.com",
        #         attachments=[],
        #         to_email_list=["sheryarbaloch67@gmail.com"],
        #     )
        # # Fetch the last EmailLog created
        # email_log = EmailLog.objects.latest("id")
        # # Call the email sending function directly
        # send_email_with_attachment_task(email_log_id=email_log.id)

        with open(
            "./apps/questionbank/tests/test_data/images/test_image.jpeg",
            "rb",
        ) as file:
            file_content = file.read()
            attachment = InMemoryUploadedFile(
                file=io.BytesIO(file_content),
                field_name="file",
                name="test_image.jpeg",
                content_type="image/jpeg",
                size=len(file_content),
                charset=None,
            )
            send_email_task(
                subject=f"Test Email from Django with attachment",
                html_content="<h1>This is a test email with attachment</h1>",
                from_email="haiderjuttearner@gmail.com",
                attachments=[attachment],
                to_email_list=["sheryarbaloch67@gmail.com"],
            )
        send_email_task(
            subject=f"Simple Test Email from Django",
            html_content="<h1>This is a simple test email</h1>",
            from_email="haiderjuttearner@gmail.com",
            attachments=[],
            to_email_list=["sheryarbaloch67@gmail.com"],
        )

        return Response()
