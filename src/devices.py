import json

from fastapi import APIRouter, Depends, Request

from src.auth import verify_token
from src.mqtt import MQTT_TOPIC_COMMAND, mqtt_client
from src.state import shared_state

router = APIRouter(prefix="/v1.0/user", dependencies=[Depends(verify_token)])


@router.get("/devices")
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
                    "description": "Умная штора на ESP32 с шаговым мотором",
                    "type": "devices.types.opening",  # Кнопка, потому что Яндекс тупой
                    "capabilities": [
                        {
                            "type": "devices.capabilities.on_off",  # Команды открыть/закрыть
                            "retrievable": True,
                            "reportable": False,
                        }
                    ],
                    "device_info": {
                        "manufacturer": "Student-Lab",
                        "model": "ESP32-ULN2003",
                        "hw_version": "1.0",
                    },
                }
            ],
        },
    }
    return payload


@router.post("/devices/query")
async def yandex_query(request: Request):
    req_id = request.headers.get("X-Request-Id", "default-req-id")
    payload = {
        "request_id": req_id,
        "payload": {
            "devices": [
                {
                    "id": "esp32_curtain_01",
                    "capabilities": [
                        {
                            "type": "devices.capabilities.on_off",
                            "state": {"instance": "on", "value": shared_state.is_open},
                        }
                    ],
                }
            ]
        },
    }
    return payload


@router.post("/devices/action")
async def yandex_action(request: Request):
    req_id = request.headers.get("X-Request-Id", "default-req-id")

    body = await request.body()
    if not body:
        return {"request_id": req_id, "payload": {"devices": []}}

    try:
        data = json.loads(body)
        device = data["payload"]["devices"][0]
        capability = device["capabilities"][0]

        shared_state.is_open = capability["state"]["value"]

        # Отправляем команду в MQTT топик ESPHome
        mqtt_command = "OPEN" if shared_state.is_open else "CLOSE"
        mqtt_client.publish(MQTT_TOPIC_COMMAND, mqtt_command)
        print(f"[MQTT] Отправлена команда {mqtt_command} в топик {MQTT_TOPIC_COMMAND}")

    # Яндекс иногда отсылает подубную дичь
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"[API] Ошибка парсинга действия от Яндекса: {e}")
        return {"request_id": req_id, "payload": {"devices": []}}

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
                                "action_result": {"status": "DONE"},
                            },
                        }
                    ],
                }
            ]
        },
    }
    return response_payload


@router.post("/unlink")
async def yandex_unlink(request: Request):
    req_id = request.headers.get("X-Request-Id", "default-req-id")
    print("[API] Запрос на отвязку аккаунта (unlink) получен")
    return {"request_id": req_id}
