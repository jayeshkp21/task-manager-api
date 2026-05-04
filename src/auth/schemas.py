from datetime import datetime
from typing import List
import uuid
from pydantic import BaseModel, Field, ConfigDict
from src.projects.schemas import ProjectModel
from src.db.models import Task, Project

class UserModel(BaseModel):
    uid: uuid.UUID
    username:str
    email:str
    first_name:str
    last_name:str
    # password_hash:str = Field(exclude=True)
    is_verified:bool = Field(default=False)
    created_at:datetime
    updated_at:datetime
    model_config = ConfigDict(from_attributes=True)
    

class UserProjectsModel(UserModel):
    projects: List[ProjectModel] = []

    model_config = ConfigDict(from_attributes=True)
    
    
class UserCreateModel(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str    
    
class UserLoginModel(BaseModel):
    email: str = Field(max_length=40)
    password: str = Field(min_length=6)
    
class EmailModel(BaseModel):
    addresses : List[str]
    
class PasswordResetModel(BaseModel):
    email: str
    
class PasswordResetConfirmModel(BaseModel):
    new_password: str
    confirm_new_password: str