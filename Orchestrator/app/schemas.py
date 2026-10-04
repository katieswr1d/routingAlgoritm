from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class PointInput(BaseModel):
    lat: float
    lon: float

class PointResponse(BaseModel):
    id: int
    lat: float
    lon: float
    score: Optional[float] = None
    label: Optional[str] = None
    is_viewpoint: bool = False

class TaskResponse(BaseModel):
    task_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    points: Optional[List[PointResponse]] = None
    route: Optional[List[dict]] = None
    total_score: Optional[float] = None
    error: Optional[str] = None

class DeletePointsRequest(BaseModel):
    point_ids: List[int]