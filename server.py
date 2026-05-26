import json
from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
import paho.mqtt.client as mqtt

app = FastAPI()

# --- НАСТРОЙКИ MQTT ---
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_USER = "jezv"
MQTT_PASS = "1122334455"
MQTT_TOPIC = "shpora_curtain/cover/curtain/command"

# Инициализация MQTT
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()


# --- ФЕЙКОВАЯ АВТОРИЗАЦИЯ (OAuth 2.0) ДЛЯ ЯНДЕКСА ---

# 1. Сюда Яндекс перенаправит вас в приложении на телефоне
@app.get("/auth")
async def yandex_oauth_auth(redirect_uri: str, state: str):
    # Скрипт ловит адрес возврата Яндекса и мгновенно отправляет его назад с фейковым кодом
    return RedirectResponse(f"{redirect_uri}?code=fake_auth_code_2026&state={state}")


# 2. Сюда сервер Яндекса постучится за токеном
@app.post("/token")
async def yandex_oauth_token(request: Request):
    # Игнорируем проверку секретов и просто отдаем Яндексу "вечный" токен (на 1 год)
    return {
        "access_token": "super_secret_master_token_2026",
        "token_type": "Bearer",
        "expires_in": 31536000
    }


# --- HTTP ЭНДПОИНТЫ УМНОГО ДОМА ---

# 3. Проверка связи
@app.head("/v1.0")
@app.get("/v1.0")
async def yandex_head():
    return Response(status_code=200)


# 4. Список устройств (Discovery)
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
                    "type": "devices.types.blind",
                    "capabilities": [
                        {
                            "type": "devices.capabilities.on_off",
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


# 5. Выполнение команды (Action)
@app.post("/v1.0/user/devices/action")
async def yandex_action(request: Request):
    data = await request.json()
    
    device = data["payload"]["devices"][0]
    capability = device["capabilities"][0]
    is_on = capability["state"]["value"]
    
    mqtt_command = "OPEN" if is_on else "CLOSE"
    mqtt_client.publish(MQTT_TOPIC, mqtt_command)
    print(f"[MQTT] Отправлена команда {mqtt_command} в топик {MQTT_TOPIC}")
    
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
