from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from src.mqtt import start_mqtt

start_mqtt()

from src.auth import router as auth_router
from src.devices import router as devices_router
from src.health import router as health_router

app = FastAPI(title="Yandex Alice MQTT Curtain Gateway")

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(devices_router)
