from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import math

# Импортируем ТВОЙ алгоритм
from router import rt_point, build_route, mark_watch_places, get_distance

app = FastAPI(title="Eco-Route Routing Service", version="1.0.0")


# ========== СХЕМЫ ==========

class PointInput(BaseModel):
    id: int
    x: float
    y: float
    rating: float
    is_viewpoint: bool = False


class RouteRequest(BaseModel):
    points: List[PointInput]
    start_point_index: int = 0
    max_steps: int = 20
    watch_distance: float = 20.0
    max_watch_places: int = 3


class RoutePointOut(BaseModel):
    id: int
    x: float
    y: float
    rating: float
    visit_count: int
    is_looped: bool
    is_loop_start: bool
    is_watch_place: bool


class RouteResponse(BaseModel):
    route_indices: List[int]
    route: List[RoutePointOut]
    total_distance: float
    average_rating: float
    watch_places: List[int]
    loops_detected: int


# ========== ЭНДПОИНТЫ ==========

@app.get("/health")
def health():
    return {"status": "ok", "service": "routing"}


@app.post("/build", response_model=RouteResponse)
def build_route_endpoint(request: RouteRequest):
    """Принимает точки, запускает ТВОЙ алгоритм, возвращает маршрут"""

    if len(request.points) < 3:
        raise HTTPException(status_code=400, detail="Минимум 3 точки")

    # Преобразуем JSON → ТВОИ объекты rt_point
    points = []
    for p in request.points:
        pt = rt_point()
        pt.rating = p.rating
        pt.coordinates = [p.x, p.y]
        pt.visit_count = 0
        pt.looped = 0
        pt.loop_start = 0
        pt.watch_place = 0
        points.append(pt)


    route_indices = build_route(
        points,
        start_point_index=request.start_point_index,
        max_steps=request.max_steps
    )

    # Помечаем смотровые площадки ТВОИМ алгоритмом
    mark_watch_places(
        points,
        route_indices,
        request.watch_distance,
        request.max_watch_places
    )

    # Собираем ответ
    route_points = [
        RoutePointOut(
            id=request.points[idx].id,
            x=points[idx].coordinates[0],
            y=points[idx].coordinates[1],
            rating=points[idx].rating,
            visit_count=points[idx].visit_count,
            is_looped=bool(points[idx].looped),
            is_loop_start=bool(points[idx].loop_start),
            is_watch_place=bool(points[idx].watch_place)
        )
        for idx in route_indices
    ]

    total_distance = sum(
        get_distance(points[route_indices[i]], points[route_indices[i + 1]])
        for i in range(len(route_indices) - 1)
    )

    return RouteResponse(
        route_indices=route_indices,
        route=route_points,
        total_distance=round(total_distance, 2),
        average_rating=round(sum(points[i].rating for i in route_indices) / len(route_indices), 2),
        watch_places=[i for i, p in enumerate(points) if p.watch_place == 1],
        loops_detected=sum(1 for p in points if p.loop_start == 1)
    )