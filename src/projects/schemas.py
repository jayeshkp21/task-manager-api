import uuid
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_PROJECT_STATUSES = ['active', 'archived']
VALID_MEMBER_ROLES = ['owner', 'admin', 'member']

class ProjectCreateModel(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)


class ProjectUpdateModel(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    status: Optional[str] = Field(default=None)
    
    @field_validator('status')
    @classmethod
    def check_status(cls, v):
        if v and v not in VALID_PROJECT_STATUSES:
            raise ValueError(f'Status must be one of {VALID_PROJECT_STATUSES}')
        return v


class ProjectModel(BaseModel):
    uid: uuid.UUID
    name: str
    description: Optional[str]
    owner_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberModel(BaseModel):
    uid: uuid.UUID
    project_uid: uuid.UUID
    user_uid: uuid.UUID
    role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailModel(ProjectModel):
    members: List[MemberModel] = []

    model_config = ConfigDict(from_attributes=True)


class AddMemberModel(BaseModel):
    user_uid: uuid.UUID
    role: str = Field(default="member")
    
    @field_validator('role')
    @classmethod
    def check_role(cls, v):
        if v not in VALID_MEMBER_ROLES:
            raise ValueError(f'Role must be one of {VALID_MEMBER_ROLES}')
        return v


class UpdateMemberRoleModel(BaseModel):
    role: str

    @field_validator('role')
    @classmethod
    def check_role(cls, v):
        if v not in VALID_MEMBER_ROLES:
            raise ValueError(f'Role must be one of {VALID_MEMBER_ROLES}')
        return v
    
class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Any]
 