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

# Глобальная переменная для хранения состояния шторы (False = закрыта, True = открыта)
CURTAIN_STATE = False

# Инициализация MQTT с поддержкой разных версий paho-mqtt
try:
    mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
except AttributeError:
    mqtt_client = mqtt.Client()

mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()


# --- OAUTH 2.0 ЭНДПОИНТЫ ---

@app.get("/auth")
async def yandex_oauth_auth(redirect_uri: str, state: str):
    return RedirectResponse(f"{redirect_uri}?code=fake_auth_code_2026&state={state}")

@app.post("/token")
async def yandex_oauth_token():
    return {
        "access_token": "super_secret_master_token_2026",
        "token_type": "Bearer",
        "expires_in": 31536000
    }


# --- SMART HOME API v1.0 ЭНДПОИНТЫ ---

# 1. Проверка связи
@app.head("/v1.0")
@app.get("/v1.0")
async def yandex_head():
    return Response(status_code=200)


# 2. Список устройств (Discovery)
@app.get("/v1.0/user/devices")
async def yandex_devices(request: Request):
    req_id = request.headers.get("X-Request-Id", "default-req-id")
    payload = {
        "request_id": req_id,
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
                            "reportable": False,
                            "parameters": {
                                "split": False  # Указываем, что это простой одноклавишный выключатель
                            }
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

# 3. Запрос состояния (Query) — ИСПРАВЛЕНО (Раньше давал 404)
@app.post("/v1.0/user/devices/query")
async def yandex_query(request: Request):
    req_id = request.headers.get("X-Request-Id", "default-req-id")
    
    # Возвращаем Алисе текущий статус нашей шторы из переменной CURTAIN_STATE
    payload = {
        "request_id": req_id,
        "payload": {
            "devices": [
                {
                    "id": "esp32_curtain_01",
                    "capabilities": [
                        {
                            "type": "devices.capabilities.on_off",
                            "state": {
                                "instance": "on",
                                "value": CURTAIN_STATE
                            }
                        }
                    ]
                }
            ]
        }
    }
    return payload


# 4. Управление (Action) — ИСПРАВЛЕНО (Защита от пустых пингов Яндекса)
@app.post("/v1.0/user/devices/action")
async def yandex_action(request: Request):
    req_id = request.headers.get("X-Request-Id", "default-req-id")
    global CURTAIN_STATE
    
    # Проверяем на пустой POST-запрос, который Яндекс шлет для проверки связи
    body = await request.body()
    if not body:
        return {"request_id": req_id, "payload": {"devices": []}}
        
    try:
        data = json.loads(body)
        device = data["payload"]["devices"][0]
        capability = device["capabilities"][0]
        
        # Запоминаем новое состояние шторы
        CURTAIN_STATE = capability["state"]["value"]
        
        mqtt_command = "OPEN" if CURTAIN_STATE else "CLOSE"
        mqtt_client.publish(MQTT_TOPIC, mqtt_command)
        print(f"[MQTT] Отправлена команда {mqtt_command} в топик {MQTT_TOPIC}")
        
    except (json.JSONDecodeError, KeyError, IndexError):
        # Если Яндекс прислал кривую структуру во время теста, не падаем в 500, а мягко отвечаем
        return {"request_id": req_id, "payload": {"devices": []}}
    
    # Корректный ответ по документации Яндекса
    response_payload = {
        "request_id": req_id,
        "payload": {
            "devices": [
                {
                    "id": "esp32_curtain_01",
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


# 5. Отвязка аккаунта (Unlink) — ИСПРАВЛЕНО (Раньше давал 404)
@app.post("/v1.0/user/unlink")
async def yandex_unlink(request: Request):
    req_id = request.headers.get("X-Request-Id", "default-req-id")
    return {"request_id": req_id}
