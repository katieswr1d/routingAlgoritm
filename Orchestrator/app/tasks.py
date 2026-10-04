from celery import Celery
import httpx
import json
from datetime import datetime
from app.config import config
from app.database import SessionLocal
from app.models import Task, Image
from app.storage import delete_task_files

celery_app = Celery('tasks', broker=config.REDIS_URL)
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


def get_db():
    return SessionLocal()


@celery_app.task(bind=True, max_retries=3)
def process_task(self, task_id: str):
    """Главная задача: обработка фотографий и построение маршрута"""

    db = get_db()
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return {"error": "Task not found"}

    try:
        # 1. Обновляем статус
        task.status = "processing"
        db.commit()

        # 2. Получаем все изображения задачи
        images = db.query(Image).filter(Image.task_id == task_id).all()

        if not images:
            task.status = "failed"
            task.error = "Нет изображений для обработки"
            db.commit()
            return {"error": "No images"}

        # 3. Отправляем каждое фото в Vision Service
        scores = []
        points_data = []

        for idx, img in enumerate(images):
            try:
                with open(img.filepath, "rb") as f:
                    response = httpx.post(
                        config.VISION_SERVICE_URL,
                        files={"file": (img.filename, f, "image/jpeg")},
                        timeout=30.0
                    )


                if response.status_code == 200:
                    data = response.json()
                    score = data.get("score", 0.0)
                    label = data.get("label", "normal")

                    img.score = score
                    img.label = label
                    db.commit()

                    scores.append(score)
                    points_data.append({
                        "id": img.id,
                        "x": img.lat,  # ← x
                        "y": img.lon,  # ← y
                        "rating": score,
                        "is_viewpoint": img.is_viewpoint
                    })
                else:
                    img.score = 0.0
                    img.label = "error"
                    db.commit()

                    scores.append(0.0)
                    points_data.append({
                        "id": img.id,
                        "x": img.lat,  # ← x (переименовал)
                        "y": img.lon,  # ← y (переименовал)
                        "rating": score,
                        "is_viewpoint": img.is_viewpoint
                    })

            except Exception as e:
                img.score = 0.0
                img.label = "error"
                db.commit()

                scores.append(0.0)
                points_data.append({
                    "id": img.id,
                    "x": img.lat,  # ← x (переименовал)
                    "y": img.lon,  # ← y (переименовал)
                    "rating": score,
                    "is_viewpoint": img.is_viewpoint
                })

        # 4. Отправляем данные в Routing Service для построения маршрута

        route = []
        total_distance = 0
        average_rating = 0

        try:
            routing_response = httpx.post(
                config.ROUTING_SERVICE_URL,
                json={
                    "points": points_data,
                    "max_steps": min(20, len(points_data)),
                    "watch_distance": 20,
                    "max_watch_places": 3
                },
                timeout=60.0
            )

            if routing_response.status_code == 200:
                route_data = routing_response.json()
                route = route_data.get("route", [])
                total_distance = route_data.get("total_distance", 0)
                average_rating = route_data.get("average_rating", 0)
                print(f"✅ Маршрут построен: {len(route)} точек, дистанция {total_distance}")
            else:
                print(f"⚠️ Routing Service вернул {routing_response.status_code}: {routing_response.text}")

        except Exception as e:
            print(f"❌ Ошибка Routing Service: {e}")

        # 🔥 Считаем total_score как СУММУ рейтингов точек маршрута
        total_score = sum(point["rating"] for point in points_data)

        # 5. Сохраняем результат
        result = {
            "points": points_data,
            "route": route,
            "total_score": total_score,          # сумма рейтингов
            "total_distance": total_distance,    # длина маршрута
            "average_rating": average_rating,    # средний рейтинг
            "images_processed": len(images)
        }

        task.status = "completed"
        task.result = json.dumps(result)
        db.commit()

        return result

    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        db.commit()
        return {"error": str(e)}
    finally:
        db.close()