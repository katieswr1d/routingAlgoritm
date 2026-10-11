# 🌲 RouteCraft

<div align="center">

**Компьютерное зрение для оценки и картирования красоты ландшафта**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![.NET](https://img.shields.io/badge/.NET-8.0-512BD4?style=for-the-badge&logo=dotnet&logoColor=white)](https://dotnet.microsoft.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

[Быстрый старт](#-быстрый-старт) · [Архитектура](#️-архитектура) · [Результаты](#-результаты) · [Публикации](#-публикации)

</div>

---

## 📖 О проекте

**RouteCraft** — автоматизированная система для проектирования экологических троп, объединяющая компьютерное зрение, алгоритмы на графах и микросервисную архитектуру.

Проект создан для **упрощения и ускорения проектирования экотроп в ООПТ** (особо охраняемых природных территориях). Система сокращает время предварительного анализа территории с **2–3 недель до минут**, делая оценку эстетики ландшафта объективной и воспроизводимой.

> **Для кого этот проект:** проектировщики экотроп, сотрудники заповедников и национальных парков, а также все, кто занимается развитием экологического туризма.

---

## 🏗️ Архитектура

```text
┌─────────────────┐
│  Пользователь   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   API Gateway   │  ← порт 8000
│    (FastAPI)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Orchestrator   │  ← порт 8001
│ (FastAPI+Celery)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│      Redis      │  ← очередь задач
│    (брокер)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Celery Worker  │
└────────┬────────┘
         │
    ┌────┴─────┐
    ▼          ▼
┌─────────┐ ┌──────────┐
│ Vision  │ │ Routing  │
│ Service │ │ Service  │
│ (C#/ML) │ │ (Python) │
│ :5001   │ │  :5002   │
└─────────┘ └──────────┘
```

---

## 🛠️ Технологический стек

| Компонент | Технология | Назначение |
|-----------|------------|------------|
| **Vision Service** | C#, ML.NET, Inception v3 | Оценка эстетики ландшафтов |
| **Routing Service** | Python, FastAPI | Построение маршрутов на графах |
| **Orchestrator** | Python, FastAPI, Celery | Управление задачами |
| **Gateway** | Python, FastAPI | Единая точка входа |
| **Очередь** | Redis | Асинхронная обработка |
| **БД** | SQLite | Хранение результатов |
| **Контейнеризация** | Docker, Docker Compose | Развёртывание |

---

## 🚀 Быстрый старт

### Требования

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0) — для разработки Vision Service
- [Python 3.11+](https://www.python.org/downloads/) — для разработки Python-сервисов

### Установка и запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/your-username/RouteCraft.git
cd RouteCraft

# 2. Создать папки для данных
mkdir data uploads

# 3. Запустить все сервисы
docker-compose up --build
```

### Проверка работы

```bash
# Gateway
curl http://localhost:8000/health

# Vision Service
curl http://localhost:5001/api/vision/health

# Routing Service
curl http://localhost:5002/health

# Orchestrator через Gateway
curl http://localhost:8000/orchestrator/health
```

### Использование

```bash
# 1. Создать файл с координатами
echo '[{"lat":55.1,"lon":37.2}]' > coords.json

# 2. Загрузить фотографии
curl -X POST http://localhost:8000/upload \
  -F "files=@photo1.png" \
  -F "coordinates=<coords.json;type=application/json"

# 3. Получить task_id и проверить статус
curl http://localhost:8000/task/{task_id}
```

---

## 📊 Результаты

<div align="center">

| Метрика | Значение |
|---------|----------|
| 📸 Датасет | 2500+ изображений |
| 🧠 Архитектура | Inception v3 |
| 🎯 Точность модели | 77,9% |
| 📉 LogLoss | снижен с 1.3 до 0.3 |
| ⚡ Обработка 1 фото | ~0.5 с |
| ⚡ Обработка 3 фото | ~1.77 с |
| 🏗️ Сервисов в системе | 6 |

</div>

---

## 📁 Структура проекта

```text
RouteCraft/
│
├── Gateway/                  # API Gateway (Python)
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── Orchestrator/             # Оркестратор + Celery
│   ├── app/
│   │   ├── main.py           # FastAPI
│   │   ├── tasks.py          # Celery-задачи
│   │   ├── models.py         # SQLAlchemy-модели
│   │   ├── database.py       # Подключение к БД
│   │   ├── config.py         # Настройки
│   │   ├── schemas.py        # Pydantic-схемы
│   │   └── storage.py        # Работа с файлами
│   ├── Dockerfile
│   └── requirements.txt
│
├── VisionService/            # Оценка эстетики (C#/ML.NET)
│   ├── Controllers/
│   ├── Services/
│   ├── Models/
│   ├── ml-assets/            # Модели (не в git)
│   ├── Dockerfile
│   └── VisionService.csproj
│
├── RoutingService/           # Построение маршрутов (Python)
│   ├── main.py
│   ├── router.py             # Алгоритм на графах
│   ├── schemas.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── data/                     # База данных (не в git)
├── uploads/                  # Загруженные фото (не в git)
│
├── docker-compose.yml
└── README.md
```

---

## 🎓 Научная основа

### Оценка эстетики ландшафта

Модель Inception v3 обучена на датасете из 2500+ размеченных изображений природных ландшафтов. Классификация на 3 класса:

- 🟢 **good** — высокая эстетическая привлекательность
- 🟡 **normal** — средняя
- 🔴 **bad** — низкая

### Алгоритм построения маршрутов

Маршрут строится на основе взвешенного графа территории:

- **Вершины** — точки с координатами и эстетическими оценками
- **Рёбра** — возможные переходы между точками
- **Задача** — найти путь, максимизирующий суммарную эстетику

Особенности алгоритма:

-  Обнаружение колец (минимум 3 уникальные точки)
-  Запрет зацикливания в двух точках
-  Учёт смотровых площадок
-  Приоритизация точек с высокой оценкой

---

## 📚 Публикации

- Царева Е.А. Компьютерное зрение для оценки и картирования красоты ландшафта // XV Конгресс молодых учёных Университета ИТМО. — 2026.

---

## 👤 Автор

<div align="center">

**Царева Екатерина Алексеевна**

🎓 Университет ИТМО  
📧 katieswr1d@yandex.ru  
🔬 Научный руководитель: Сорокин Роман Борисович

</div>

---

## 📄 Лицензия

Проект распространяется под лицензией MIT. См. [LICENSE](LICENSE).

---

## 🙏 Благодарности

- Университет ИТМО
- Научный руководитель Сорокин Р.Б.
- Сообщество ML.NET и FastAPI

---

<div align="center">

Сделано с 💚 для сохранения природы

⭐ Поставь звезду, если проект тебе полезен!

</div>
