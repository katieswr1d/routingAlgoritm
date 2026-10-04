import os
import json
import uuid
from typing import List
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# ============================================================
# НАСТРОЙКИ
# ============================================================

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:8001")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10 MB

# ============================================================
# ПРИЛОЖЕНИЕ FASTAPI
# ============================================================

app = FastAPI(
    title="Eco-Route Gateway",
    description="Внешний шлюз для Eco-Route API",
    version="1.0.0"
)

# Разрешаем CORS (для фронтенда)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def validate_coordinates(coords_str: str) -> list:
    """Проверяет, что координаты — валидный JSON-массив"""
    print(f"DEBUG: coordinates raw = {coords_str}")
    try:

        coords = json.loads(coords_str)
        if not isinstance(coords, list):
            raise ValueError("coordinates должны быть массивом")
        if len(coords) == 0:
            raise ValueError("coordinates не может быть пустым")
        for item in coords:
            if "lat" not in item or "lon" not in item:
                raise ValueError("Каждая точка должна содержать lat и lon")
        return coords
    except json.JSONDecodeError:
        raise ValueError("Неверный JSON-формат coordinates")


async def forward_request(method: str, path: str, **kwargs):
    """Перенаправляет запрос в Оркестратор"""
    url = f"{ORCHESTRATOR_URL}{path}"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.request(method, url, **kwargs)

        return JSONResponse(
            status_code=response.status_code,
            content=response.json() if response.content else {}
        )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Оркестратор не отвечает (таймаут)")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Оркестратор недоступен")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка проксирования: {str(e)}")


# ============================================================
# ЭНДПОИНТЫ
# ============================================================

@app.get("/health")
async def health():
    """Проверка работоспособности Gateway"""
    return {
        "status": "ok",
        "service": "gateway",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/orchestrator/health")
async def orchestrator_health():
    """Проверка доступности Оркестратора"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/health")
        return {
            "gateway": "ok",
            "orchestrator": "ok" if response.status_code == 200 else "unhealthy"
        }
    except Exception:
        return {
            "gateway": "ok",
            "orchestrator": "unavailable"
        }


@app.post("/upload")
async def upload(
        files: List[UploadFile] = File(..., description="Фотографии (максимум 10 шт, каждая до 10 МБ)"),
        coordinates: str = Form(..., description="JSON-массив координат: [{\"lat\":55.1,\"lon\":37.2}]")
):

    """
    Загрузка фотографий и координат.

    - Максимум 10 фотографий за раз
    - Каждая фотография до 10 МБ
    - Количество координат должно совпадать с количеством фотографий
    """

    # 1. Валидация количества файлов
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="Не загружено ни одного файла")
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Максимум 10 фотографий за раз")

    # 2. Валидация координат
    try:
        coords_data = validate_coordinates(coordinates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3. Проверка совпадения количества
    if len(files) != len(coords_data):
        raise HTTPException(
            status_code=400,
            detail=f"Количество фотографий ({len(files)}) не совпадает с количеством координат ({len(coords_data)})"
        )

    # 4. Проверка размеров файлов
    for file in files:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Файл {file.filename} превышает 10 МБ"
            )
        # Возвращаем указатель в начало, чтобы можно было отправить дальше
        await file.seek(0)

    # 5. Перенаправляем в Оркестратор
    try:
        # Подготавливаем файлы для отправки
        files_for_upload = []
        for file in files:
            content = await file.read()
            files_for_upload.append(
                ("files", (file.filename, content, file.content_type or "image/jpeg"))
            )
            await file.seek(0)  # на всякий случай

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{ORCHESTRATOR_URL}/upload",
                files=files_for_upload,
                data={"coordinates": coordinates}
            )

        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Оркестратор не отвечает (таймаут)")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Оркестратор недоступен")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при отправке в Оркестратор: {str(e)}")


@app.get("/task/{task_id}")
async def get_task(task_id: str):
    """
    Получение статуса задачи по ID.
    """
    return await forward_request("GET", f"/task/{task_id}")


@app.get("/task/{task_id}/points")
async def get_points(task_id: str):
    """
    Получение списка всех точек задачи.
    """
    return await forward_request("GET", f"/task/{task_id}/points")


@app.delete("/task/{task_id}/points")
async def delete_points(task_id: str, request: Request):
    """
    Удаление точек из задачи.
    Тело запроса: {"point_ids": [1, 2, 3]}
    """
    try:
        body = await request.json()
        point_ids = body.get("point_ids", [])

        if not point_ids:
            raise HTTPException(status_code=400, detail="Не указаны point_ids")

        return await forward_request("DELETE", f"/task/{task_id}/points", json={"point_ids": point_ids})

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Неверный JSON-формат")


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)