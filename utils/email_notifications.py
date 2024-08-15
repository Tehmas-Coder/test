import json

from decouple import config

from utils.notification_utils import send_email_notification_to_list

# ! ------------------------------------------------------------
# *                 Email Notification
# ! ------------------------------------------------------------


class EmailNotification:

    # ! ------------------------------------------------------------
    # *                 CONSTRUCTOR
    # ! ------------------------------------------------------------

    def __init__(self, send_email_data_dict: dict = {}):
        self.send_email_data_dict = send_email_data_dict

        self.first_name = self.send_email_data_dict["first_name"]
        self.last_name = self.send_email_data_dict["last_name"]
        self.user_email = self.send_email_data_dict["email"]

        self.subject = ""

    # ! ------------------------------------------------------------
    # *                 PUBLIC METHODS
    # ! ------------------------------------------------------------

    def send_otp(self):
        self.html_content = self.__generate_html_content_for_otp()
        self.subject = "Question-Bank : On-Boarding"
        return self.__send_email(self.subject, self.html_content, self.user_email)

    def send_url(self):
        self.html_content = self.__generate_html_content_for_url()
        self.subject = "Question-Bank : On-Boarding"
        return self.__send_email(self.subject, self.html_content, self.user_email)

    # ! ------------------------------------------------------------
    # *                 PRIVATE METHODS
    # ! ------------------------------------------------------------

    def __generate_html_content_for_otp(self):
        with open("./email_templates/otp_email.html", "r", encoding="utf-8") as file:
            html_content = (
                file.read()
                .replace("{FIRST_NAME}", self.first_name)
                .replace("{LAST_NAME}", self.last_name)
                .replace("{EMAIL}", self.user_email)
                .replace("{OTP}", self.send_email_data_dict["OTP"])
            )
        return html_content

    def __generate_html_content_for_url(self):
        with open("./email_templates/link_email.html", "r", encoding="utf-8") as file:
            html_content = (
                file.read()
                .replace("{FIRST_NAME}", self.first_name)
                .replace("{LAST_NAME}", self.last_name)
                .replace("{EMAIL}", self.user_email)
                .replace("{PASSWORD}", self.send_email_data_dict["password"])
                .replace("{URL}", self.send_email_data_dict["URL"])
            )
        return html_content

    # ! ------------------------------------------------------------
    # *                 FORWARD EMAIL
    # ! ------------------------------------------------------------

    def __send_email(self, subject, html_content, user_email):
        self.to_email_list = [user_email]
        self.from_email = config("SYSTEM_EMAIL")
        email_body = ""

        return send_email_notification_to_list(subject, email_body, html_content, self.to_email_list, self.from_email, True)
