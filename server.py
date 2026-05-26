import json
from fastapi import FastAPI, Request, Response
import paho.mqtt.client as mqtt

app = FastAPI()

# --- НАСТРОЙКИ MQTT ---
MQTT_BROKER = "127.0.0.1"  # так как брокер на этом же мини-ПК
MQTT_PORT = 1883
MQTT_USER = "jezv"
MQTT_PASS = "1122334455"
MQTT_TOPIC = "shpora_curtain/cover/curtain/command"

# Инициализация MQTT Клиента
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()


# --- ЭНДПОИНТЫ ДЛЯ ЯНДЕКСА (Smart Home API) ---

# 1. Проверка связи (Яндекс делает этот запрос при привязке навыка)
@get("/v1.0")
async def yandex_head():
    return Response(status_code=200)


# 2. Список устройств (Яндекс спрашивает, какие устройства у нас есть)
@get("/v1.0/user/devices")
async def yandex_devices():
    payload = {
        "request_id": "shpora-req-001",
        "payload": {
            "user_id": "student_project",
            "devices": [
                {
                    "id": "esp32_curtain_01",
                    "name": "Штора",
                    "description": "Шаговый мотор на ESP32",
                    "type": "devices.types.blind",  # Тип: Рулонные шторы/жалюзи
                    "capabilities": [
                        {
                            "type": "devices.capabilities.toggle",
                            "retrievable": True,
                            "parameters": {
                                "instance": "controls",
                                "name": "открытие/закрытие"
                            }
                        }
                    ]
                }
            ]
        }
    }
    return payload


# 3. Управление (Яндекс посылает сюда команду, когда вы говорите "Алиса, закрой штору")
@post("/v1.0/user/devices/action")
async def yandex_action(request: Request):
    data = await request.json()
    
    # Парсим команду от Яндекса
    device_action = data["payload"]["devices"][0]["capabilities"][0]
    is_on = device_action["state"]["value"] # True — открыть / Включить, False — закрыть
    
    # Формируем команду для ESPHome (OPEN / CLOSE — стандартные команды для компонента cover)
    mqtt_command = "OPEN" if is_on else "CLOSE"
    
    # Отправляем в топик MQTT
    mqtt_client.publish(MQTT_TOPIC, mqtt_command)
    print(f"[MQTT] Отправлена команда: {mqtt_command} в топик {MQTT_TOPIC}")
    
    # Отвечаем Яндексу, что всё прошло успешно
    response_payload = {
        "request_id": data["request_id"],
        "payload": {
            "devices": [
                {
                    "id": "esp32_curtain_01",
                    "capabilities": [
                        {
                            "type": "devices.capabilities.toggle",
                            "state": {
                                "instance": "controls",
                                "action_result": {
                                    "status": "DONE"
                                }
                            }
                        }
                    ]
                }
            ]
        }
    }
    return response_payload
