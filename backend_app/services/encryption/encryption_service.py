from django.conf import settings
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

from backend_app.services.logging.logging_service import LoggerService

logger = LoggerService.get_logger()
KEY_LENGTH = 32


def encrypt_AESCBC(to_encrypt: str):
    """Encrypt plaintext using AES-256-CBC."""
    try:
        key = str(settings.CRYPTO_AES_SECRET_KEY).encode("utf-8")[:32].ljust(32, b"\0")
        iv = bytes.fromhex(settings.CRYPTO_AES_IV)

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(to_encrypt.encode("utf-8")) + padder.finalize()

        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        return encrypted.hex()
    except Exception as e:
        logger.error(f"Could not ENCRYPT provided data. REASON : {e}")
        raise Exception(e)


def decrypt_AESCBC(to_decrypt: str, iv=None):
    """Decrypt encrypted data using AES-256-CBC."""
    try:
        key = str(settings.CRYPTO_AES_SECRET_KEY).encode("utf-8")[:32].ljust(32, b"\0")
        iv = bytes.fromhex(iv) if iv else bytes.fromhex(settings.CRYPTO_AES_IV)

        encrypted = bytes.fromhex(to_decrypt)

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        padded_data = decryptor.update(encrypted) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()

        return data.decode("utf-8")
    except Exception as e:
        logger.error(f"Could not DECRYPT provided data. REASON : {e}")
        raise Exception(e)
