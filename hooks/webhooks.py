import json
from dataclasses import dataclass

import requests

from utils.rna_utils import decrypt_message, encrypt_message


@dataclass
class GenericWebhook:
    """
    Generic Webhook class to send data to any webhook
    """

    data_dict: dict

    def send_request(self, encryption_key: str, token: str) -> bool:
        """
        Send a POST request to the webhook URL with the encrypted data

        :param encryption_key: The encryption key to encrypt the data
        :param token: The token to decrypt the webhook URL
        :return: True if the request was successful, False otherwise
        """
        webhook_url = decrypt_message(token, encryption_key)
        encrypted_data = encrypt_message(json.dumps(self.data_dict), encryption_key)
        response = requests.post(webhook_url, json=encrypted_data)
        return True if response.status_code == 200 else False
