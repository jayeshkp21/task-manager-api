import uuid
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class CommentCreateModel(BaseModel):
    content: str = Field(min_length=1, max_length=1000)

class CommentModel(BaseModel):
    uid: uuid.UUID
    content: str
    task_uid: uuid.UUID
    author_uid: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
