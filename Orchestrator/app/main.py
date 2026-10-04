import os
import json
import uuid
from typing import List
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import config
from app.database import get_db, init_db
from app.models import Task, Image
from app.schemas import TaskResponse, PointResponse, DeletePointsRequest
from app.storage import ensure_upload_folder, save_file, delete_task_files
from app.tasks import process_task

# Создаём приложение
app = FastAPI(
    title="Eco-Route Orchestrator",
    description="Центральный сервис для управления задачами",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация
ensure_upload_folder()
init_db()


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def validate_coordinates(coords_str: str) -> list:
    """Проверяет, что координаты — валидный JSON-массив"""
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


# ============================================================
# ЭНДПОИНТЫ
# ============================================================

@app.get("/health")
async def health():
    """Проверка работоспособности Оркестратора"""
    return {
        "status": "ok",
        "service": "orchestrator",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/upload")
async def upload(
        files: List[UploadFile] = File(...),
        coordinates: str = Form(...)
):
    """
    Загрузка фотографий и координат.
    Создаёт задачу и запускает обработку в фоне.
    """
    db = next(get_db())

    # 1. Валидация
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="Не загружено ни одного файла")
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Максимум 10 фотографий за раз")

    try:
        coords_data = validate_coordinates(coordinates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if len(files) != len(coords_data):
        raise HTTPException(
            status_code=400,
            detail=f"Количество фотографий ({len(files)}) не совпадает с количеством координат ({len(coords_data)})"
        )

    # 2. Создаём задачу
    task_id = str(uuid.uuid4())
    task = Task(id=task_id, status="pending")
    db.add(task)
    db.commit()

    # 3. Сохраняем файлы
    for file, coord in zip(files, coords_data):
        content = await file.read()
        if len(content) > config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Файл {file.filename} превышает 10 МБ"
            )

        filepath = save_file(task_id, file.filename, content)

        image = Image(
            task_id=task_id,
            filename=file.filename,
            filepath=filepath,
            lat=coord["lat"],
            lon=coord["lon"],
            is_viewpoint=False
        )
        db.add(image)

    db.commit()

    # 4. Запускаем фоновую обработку
    process_task.delay(task_id)

    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Задача принята в обработку"
    }


@app.get("/task/{task_id}")
async def get_task(task_id: str):
    """Получение статуса и результата задачи"""
    db = next(get_db())
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    result = {
        "task_id": task.id,
        "status": task.status,
        "created_at": task.created_at,
        "updated_at": task.updated_at
    }

    if task.status == "completed" and task.result:
        try:
            result_data = json.loads(task.result)
            result["points"] = result_data.get("points", [])
            result["route"] = result_data.get("route", [])
            result["total_score"] = result_data.get("total_score", 0)
        except:
            pass

    if task.error:
        result["error"] = task.error

    return result


@app.get("/task/{task_id}/points")
async def get_points(task_id: str):
    """Получение списка всех точек задачи"""
    db = next(get_db())
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    images = db.query(Image).filter(Image.task_id == task_id).all()

    points = [
        {
            "id": img.id,
            "lat": img.lat,
            "lon": img.lon,
            "score": img.score,
            "label": img.label,
            "is_viewpoint": img.is_viewpoint,
            "filename": img.filename
        }
        for img in images
    ]

    return {
        "task_id": task_id,
        "points": points
    }


@app.delete("/task/{task_id}/points")
async def delete_points(task_id: str, request: DeletePointsRequest):
    """Удаление точек из задачи и перестроение маршрута"""
    db = next(get_db())

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    if task.status == "completed":
        raise HTTPException(status_code=400, detail="Нельзя удалять точки из завершённой задачи")

    # Удаляем точки
    for point_id in request.point_ids:
        image = db.query(Image).filter(
            Image.id == point_id,
            Image.task_id == task_id
        ).first()
        if image:
            # Удаляем файл
            if os.path.exists(image.filepath):
                os.remove(image.filepath)
            db.delete(image)

    db.commit()

    # Проверяем, остались ли точки
    remaining = db.query(Image).filter(Image.task_id == task_id).count()

    if remaining == 0:
        task.status = "failed"
        task.error = "Все точки удалены"
        db.commit()
        return {
            "task_id": task_id,
            "status": "failed",
            "message": "Все точки удалены, маршрут не может быть построен",
            "remaining_points": 0
        }

    # Перезапускаем обработку с оставшимися точками
    task.status = "pending"
    task.result = None
    task.error = None
    db.commit()

    process_task.delay(task_id)

    return {
        "task_id": task_id,
        "status": "pending",
        "message": f"Точки удалены, обработка перезапущена с {remaining} точками",
        "remaining_points": remaining
    }