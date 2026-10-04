from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    result = Column(Text, nullable=True)  # JSON с результатом
    error = Column(Text, nullable=True)


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"))
    filename = Column(String)
    filepath = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    score = Column(Float, nullable=True)  # оценка от Vision Service (0-1)
    label = Column(String, nullable=True)  # good/normal/bad
    is_viewpoint = Column(Boolean, default=False)

    task = relationship("Task", backref="images")


def init_db():
    from app.database import engine
    Base.metadata.create_all(bind=engine)