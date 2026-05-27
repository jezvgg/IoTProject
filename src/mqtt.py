import os

import paho.mqtt.client as mqtt

from src.state import shared_state

MQTT_BROKER = os.getenv("MQTT_BROKER", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "example_user")
MQTT_PASS = os.getenv("MQTT_PASS", "example_password")
MQTT_TOPIC_COMMAND = os.getenv(
    "MQTT_TOPIC_COMMAND", "shpora_curtain/cover/curtain/command"
)
MQTT_TOPIC_STATE = os.getenv("MQTT_TOPIC_STATE", "shpora_curtain/cover/curtain/state")


def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Успешно подключено к MQTT брокеру с кодом {rc}")
    client.subscribe(MQTT_TOPIC_STATE)
    print(f"[MQTT] Подписались на топик статуса: {MQTT_TOPIC_STATE}")


def on_message(client, userdata, msg):
    payload = msg.payload.decode().strip()
    match payload:
        case "open":
            shared_state.is_open = True
            print("[STATE] Статус шторы обновлен: ОТКРЫТА")
        case "closed":
            shared_state.is_open = False
            print("[STATE] Статус шторы обновлен: ЗАКРЫТА")


# Совместимость с paho-mqtt v2 и v1
callback_api_version = getattr(mqtt, "CallbackAPIVersion", None)
if callback_api_version is not None:
    mqtt_client = mqtt.Client(callback_api_version=callback_api_version.VERSION1)
else:
    mqtt_client = mqtt.Client()

mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


def start_mqtt():
    mqtt_client.connect_async(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    print(f"[MQTT] Запущен процесс подключения к {MQTT_BROKER}:{MQTT_PORT}...")
