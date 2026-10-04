from pydantic import BaseModel
from typing import List, Optional

class PointInput(BaseModel):
    """Точка на вход (от Оркестратора)"""
    id: int
    x: float              # координата X
    y: float              # координата Y
    rating: float           # 0.1 / 0.5 / 1.0 (bad / normal / good)
    is_viewpoint: bool = False

class RouteRequest(BaseModel):
    """Запрос на построение маршрута"""
    points: List[PointInput]
    start_point_id: Optional[int] = None   # если None — берём первую good
    max_steps: int = 20
    watch_distance: float = 20.0           # WD
    max_watch_places: int = 3              # WN

class RoutePoint(BaseModel):
    """Точка в маршруте (на выход)"""
    id: int
    x: float
    y: float
    rating: float
    visit_count: int
    is_looped: bool
    is_loop_start: bool
    is_watch_place: bool

class RouteResponse(BaseModel):
    """Ответ с маршрутом"""
    route: List[RoutePoint]
    route_indices: List[int]
    total_distance: float
    average_rating: float
    unique_points_visited: int
    watch_places: List[int]
    loops_detected: int