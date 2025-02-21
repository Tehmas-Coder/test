from core.settings import ENCRYPTION_KEY


def get_encryption_key():
    """
    Get the encryption key from the settings file

    :return: The encryption key (str)
    """
    return ENCRYPTION_KEY
