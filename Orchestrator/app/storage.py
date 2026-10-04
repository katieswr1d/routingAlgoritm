import os
import shutil
from pathlib import Path
from app.config import config


def ensure_upload_folder():
    """Создаёт папку для загрузок, если её нет"""
    Path(config.UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)


def get_task_folder(task_id: str) -> str:
    """Возвращает путь к папке задачи"""
    return os.path.join(config.UPLOAD_FOLDER, task_id)


def ensure_task_folder(task_id: str):
    """Создаёт папку для задачи"""
    Path(get_task_folder(task_id)).mkdir(parents=True, exist_ok=True)


def save_file(task_id: str, filename: str, content: bytes) -> str:
    """Сохраняет файл в папку задачи"""
    task_folder = get_task_folder(task_id)
    Path(task_folder).mkdir(parents=True, exist_ok=True)

    filepath = os.path.join(task_folder, filename)
    with open(filepath, "wb") as f:
        f.write(content)
    return filepath


def delete_task_files(task_id: str):
    """Удаляет все файлы задачи"""
    task_folder = get_task_folder(task_id)
    if os.path.exists(task_folder):
        shutil.rmtree(task_folder)