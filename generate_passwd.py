import base64
import hashlib
import os


def create_passwd_file(username: str, password: str, filepath: str):
    iterations = 10100
    salt = os.urandom(12)
    key = hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), salt, iterations)

    iter_b64 = (
        base64.b64encode(iterations.to_bytes(4, byteorder="big"))
        .decode("utf-8")
        .rstrip("=")
    )
    salt_b64 = base64.b64encode(salt).decode("utf-8").rstrip("=")
    key_b64 = base64.b64encode(key).decode("utf-8").rstrip("=")

    hash_str = f"{username}:$7${iter_b64}${salt_b64}${key_b64}\n"

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(hash_str)

    print(f"[SUCCESS] Файл паролей успешно создан по пути: {filepath}")
    print(f"Пользователь: {username}")


if __name__ == "__main__":
    MQTT_USER = os.getenv("MQTT_USER", "jezv")
    MQTT_PASS = os.getenv("MQTT_PASS", "1122334455")

    create_passwd_file(MQTT_USER, MQTT_PASS, "mosquitto/config/passwd")
