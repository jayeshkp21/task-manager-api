from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship, Column
import sqlalchemy.dialects.postgresql as pg
from datetime import datetime, date
import uuid

class User(SQLModel, table=True):
    __tablename__ = "users"
    uid: uuid.UUID = Field(
        sa_column=Column(pg.UUID, nullable=False, primary_key=True, default=uuid.uuid4)
    )
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    first_name: str
    last_name: str
    password_hash: str = Field(sa_column=Column(pg.VARCHAR, nullable=False))
    role: str = Field(sa_column=Column(pg.VARCHAR, nullable=False, server_default="member"))
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    projects: List["Project"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"lazy": "selectin"}
    )

    def __repr__(self):
        return f"Username: {self.username}"


class Project(SQLModel, table=True):
    __tablename__ = "projects"
    uid: uuid.UUID = Field(
        sa_column=Column(pg.UUID, nullable=False, primary_key=True, default=uuid.uuid4)
    )
    name: str
    description: Optional[str] = None
    owner_id: uuid.UUID = Field(foreign_key="users.uid")
    status: str = Field(sa_column=Column(pg.VARCHAR, nullable=False, server_default="active"))      
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    owner: Optional[User] = Relationship(
        back_populates="projects",
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    members: List["ProjectMember"] = Relationship(      
        sa_relationship_kwargs={"lazy": "selectin", "cascade":"all, delete-orphan"}
    )                                                   
    tasks: List["Task"] = Relationship(                 
        sa_relationship_kwargs={"lazy": "selectin", "cascade":"all, delete-orphan"}     
    )                                                   

    def __repr__(self):
        return f"Project: {self.name}"


class ProjectMember(SQLModel, table=True):
    __tablename__ = "project_members"
    uid: uuid.UUID = Field(
        sa_column=Column(pg.UUID, nullable=False, primary_key=True, default=uuid.uuid4)
    )
    project_uid: uuid.UUID = Field(foreign_key="projects.uid")
    user_uid: uuid.UUID = Field(foreign_key="users.uid")
    role: str = Field(sa_column=Column(pg.VARCHAR, nullable=False, server_default="member"))
    joined_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))


class Task(SQLModel, table=True):
    __tablename__ = "tasks"
    uid: uuid.UUID = Field(
        sa_column=Column(pg.UUID, nullable=False, primary_key=True, default=uuid.uuid4)
    )
    title: str
    description: Optional[str] = None
    project_uid: uuid.UUID = Field(foreign_key="projects.uid")
    assigned_to: Optional[uuid.UUID] = Field(default=None, foreign_key="users.uid")
    created_by: uuid.UUID = Field(foreign_key="users.uid")
    status: str = Field(sa_column=Column(pg.VARCHAR, nullable=False, server_default="todo"))
    priority: str = Field(sa_column=Column(pg.VARCHAR, nullable=False, server_default="medium"))
    due_date: Optional[date] = Field(default=None, nullable=True)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    comments: List['Comment'] = Relationship(sa_relationship_kwargs={'lazy': 'selectin', 'cascade': 'all, delete-orphan'})

    def __repr__(self):
        return f"Task: {self.title}"
    

class Comment(SQLModel, table=True):
    __tablename__ = 'comments'
    uid: uuid.UUID = Field(sa_column=Column(pg.UUID, primary_key=True, default=uuid.uuid4))
    content: str
    task_uid: uuid.UUID = Field(foreign_key='tasks.uid')
    author_uid: uuid.UUID = Field(foreign_key='users.uid')
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    
    def __repr__(self):
        return f"Comment by {self.author_uid} on task {self.task_uid}"
    
class TaskActivity(SQLModel, table=True):
    __tablename__ = 'task_activities'
    uid: uuid.UUID = Field(sa_column=Column(pg.UUID, primary_key=True, default=uuid.uuid4))
    task_uid: uuid.UUID = Field(foreign_key='tasks.uid')
    user_uid: uuid.UUID = Field(foreign_key='users.uid')
    action: str       # e.g. 'status_changed', 'assigned', 'priority_changed'
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))

    def __repr__(self):
        return f"Activity: {self.action} by {self.user_uid} on task {self.task_uid}"
    
