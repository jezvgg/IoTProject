from fastapi import APIRouter, Response

router = APIRouter()


@router.head("/v1.0")
@router.get("/v1.0")
async def yandex_head():
    return Response(status_code=200)
