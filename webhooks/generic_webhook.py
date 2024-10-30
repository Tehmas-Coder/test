import json
from dataclasses import dataclass

import requests

from utils.rna_utils import decrypt_message, encrypt_message


@dataclass
class GenericWebhook:
    data_dict: dict

    def send_request(self, encryption_key: str, token: str) -> bool:
        webhook_url = decrypt_message(token, encryption_key)
        encrypted_data = encrypt_message(json.dumps(self.data_dict), encryption_key)
        response = requests.post(webhook_url, json=encrypted_data)
        return True if response.status_code == 200 else False
