import hashlib
import base64
import json

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

_KEY = hashlib.md5("school-quiz-answer-key-2024".encode()).hexdigest().encode()


def decrypt_answer(encrypted_text: str, question_type: str):
    """
    解密题目答案，根据题型返回不同格式：
      single_choice / true_false → str，如 "B" / "false"
      multiple_choice            → list，如 ["A", "B", "C"]
    """
    raw_bytes = base64.b64decode(encrypted_text)
    decrypted = unpad(AES.new(_KEY, AES.MODE_ECB).decrypt(raw_bytes), 16).decode("utf-8")

    if question_type == "multiple_choice":
        return json.loads(decrypted)   # "[\"A\",\"B\"]" → ["A", "B"]
    return decrypted                   # "B" / "false"
