import json
from fastapi import FastAPI, Request, Response
import paho.mqtt.client as mqtt

app = FastAPI()

# --- НАСТРОЙКИ MQTT ---
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_USER = "ваш_логин"
MQTT_PASS = "ваш_пароль"
MQTT_TOPIC = "shpora_curtain/cover/curtain/command"

# Инициализация MQTT
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()


# --- HTTP ЭНДПОИНТЫ ДЛЯ ЯНДЕКСА ---

# 1. Проверка связи (HEAD/GET запрос)
@app.head("/v1.0")
@app.get("/v1.0")
async def yandex_head():
    # Яндекс требует просто 200 OK в ответ на этот запрос
    return Response(status_code=200)


# 2. Список устройств (Discovery)
@app.get("/v1.0/user/devices")
async def yandex_devices():
    payload = {
        "request_id": "shpora-req-unique-id",
        "payload": {
            "user_id": "student_project_id",
            "devices": [
                {
                    "id": "esp32_curtain_01",
                    "name": "Штора",
                    "description": "Шаговый мотор на ESP32 через MQTT",
                    "type": "devices.types.blind",  # Тип устройства: Шторы
                    "capabilities": [
                        {
                            "type": "devices.capabilities.on_off",  # Стандартное умение Вкл/Выкл
                            "retrievable": True,
                            "reportable": False
                        }
                    ],
                    "device_info": {
                        "manufacturer": "Student-Lab",
                        "model": "ESP32-ULN2003",
                        "hw_version": "1.0"
                    }
                }
            ]
        }
    }
    return payload


# 3. Выполнение команды (Action)
@app.post("/v1.0/user/devices/action")
async def yandex_action(request: Request):
    data = await request.json()
    
    # Извлекаем данные из строгого JSON Яндекса
    device = data["payload"]["devices"][0]
    capability = device["capabilities"][0]
    
    # Получаем состояние: True (Включено/Открыто) или False (Выключено/Закрыто)
    is_on = capability["state"]["value"]
    
    # Отправляем понятную для ESPHome команду в MQTT топик
    mqtt_command = "OPEN" if is_on else "CLOSE"
    mqtt_client.publish(MQTT_TOPIC, mqtt_command)
    print(f"[MQTT] Отправлена команда {mqtt_command} в топик {MQTT_TOPIC}")
    
    # Строгий формат ответа Яндексу об успешном выполнении
    response_payload = {
        "request_id": data["request_id"],
        "payload": {
            "devices": [
                {
                    "id": device["id"],
                    "capabilities": [
                        {
                            "type": "devices.capabilities.on_off",
                            "state": {
                                "instance": "on",
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
