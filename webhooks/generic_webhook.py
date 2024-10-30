from dataclasses import dataclass

import requests
from cryptography.fernet import Fernet


@dataclass
class GenericWebhook:
    data_dict: dict

    def send_request(self, encryption_key: str, token: str) -> bool:
        webhook_url = self.__decrypt_token(encryption_key, token)
        response = requests.post(webhook_url, json=self.data_dict)
        return True if response.status_code == 200 else False

    def __decrypt_token(self, encryption_key, token) -> str:
        decoded_key = encryption_key[1:]
        cipher = Fernet(decoded_key)
        decrypted_message = cipher.decrypt(token).decode()
        return decrypted_message
