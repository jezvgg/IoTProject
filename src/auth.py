import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter()

YANDEX_TOKEN = os.getenv("YANDEX_TOKEN", "super_secret_master_token_2026")

security = HTTPBearer()

# Имитация OAuth2 для Яндекса


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != YANDEX_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/auth")
async def yandex_oauth_auth(redirect_uri: str, state: str):
    return RedirectResponse(f"{redirect_uri}?code=fake_auth_code_2026&state={state}")


@router.post("/token")
async def yandex_oauth_token():
    return {
        "access_token": YANDEX_TOKEN,
        "token_type": "Bearer",
        "expires_in": 31536000,
    }
