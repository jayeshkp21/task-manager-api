import uuid
from datetime import datetime, date
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


VALID_STATUSES = ["todo", "in_progress", "in_review", "done"]
VALID_PRIORITIES = ["low", "medium", "high", "critical"]

class TaskCreateModel(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    priority: str = Field(default="medium")
    assigned_to: Optional[uuid.UUID] = None
    due_date: Optional[date] = None

    @field_validator("priority")
    @classmethod
    def check_priority(cls, v):
        if v not in VALID_PRIORITIES:
            raise ValueError(f"Must be one of {VALID_PRIORITIES}")
        return v

class TaskUpdateModel(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    due_date: Optional[date] = None


class TaskModel(BaseModel):
    uid: uuid.UUID
    title: str
    description: Optional[str]
    project_uid: uuid.UUID
    assigned_to: Optional[uuid.UUID]
    created_by: uuid.UUID
    status: str
    priority: str
    due_date: Optional[date]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Any]