import os


class Config:
    # URLs других сервисов
    VISION_SERVICE_URL = os.getenv("VISION_URL", "http://vision-service:5001/api/vision/assess")
    ROUTING_SERVICE_URL = os.getenv("ROUTING_URL", "http://routing-service:5002/build")

    # Redis (для Celery)
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # База данных
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////app/data/orchestrator.db")

    # Папка для загрузок
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")

    # Максимальный размер файла (10 МБ)
    MAX_FILE_SIZE = 10 * 1024 * 1024


config = Config()