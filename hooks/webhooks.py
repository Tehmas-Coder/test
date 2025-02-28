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
        Sends an encrypted request to a webhook URL.

        This function decrypts the provided token to obtain the webhook URL,
        encrypts the data dictionary, and sends it as a POST request to the
        webhook URL.

        Args:
            encryption_key (str): The key used for encryption and decryption.
            token (str): The encrypted token containing the webhook URL.

        Returns:
            bool: True if the request was successful (status code 200), False otherwise.
        """
        webhook_url = decrypt_message(token, encryption_key)
        encrypted_data = encrypt_message(json.dumps(self.data_dict), encryption_key)
        response = requests.post(webhook_url, json=encrypted_data)
        return True if response.status_code == 200 else False
