import uuid
from typing import Optional
from sentry_sdk import session
from sqlmodel import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import Task, TaskActivity
from .schemas import TaskCreateModel, TaskUpdateModel, VALID_STATUSES, VALID_PRIORITIES
from datetime import datetime


class TaskService:

    async def get_project_tasks(
        self,
        project_uid: uuid.UUID,
        session: AsyncSession,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[str] = None,
        page: int = 1, 
        page_size: int = 20,
    ):
        """Get all tasks for a project with optional filters."""
        statement = select(Task).where(Task.project_uid == project_uid)

        if status:
            statement = statement.where(Task.status == status)
        if priority:
            statement = statement.where(Task.priority == priority)
        if assigned_to:
            statement = statement.where(Task.assigned_to == assigned_to)
            
        count_statement = select(func.count()).select_from(Task).where(Task.project_uid == project_uid)
        total = await session.scalar(count_statement)
        
        statement = statement.offset((page - 1) * page_size).limit(page_size)

        result = await session.execute(statement)
        tasks = result.scalars().all()
        return tasks, total

    async def get_task(self, task_uid: uuid.UUID, session: AsyncSession):
        """Get a single task by uid."""
        statement = select(Task).where(Task.uid == task_uid)
        result = await session.execute(statement)
        return result.scalars().first()

    async def create_task(
        self,
        task_data: TaskCreateModel,
        project_uid: uuid.UUID,
        created_by: uuid.UUID,
        session: AsyncSession,
    ):
        """Create a task inside a project."""
        task_data_dict = task_data.model_dump()
        new_task = Task(
            **task_data_dict,
            project_uid=project_uid,
            created_by=created_by,
        )
        session.add(new_task)
        await session.commit()
        await session.refresh(new_task)
        return new_task

    async def update_task(
        self, task: Task, update_data: TaskUpdateModel, user_uid: uuid.UUID, session: AsyncSession
    ):
        """Update a task. Validates status and priority values, logs activity."""
        update_dict = update_data.model_dump(exclude_unset=True)

        if "status" in update_dict and update_dict["status"] not in VALID_STATUSES:
            raise ValueError(f"Status must be one of {VALID_STATUSES}")
        if "priority" in update_dict and update_dict["priority"] not in VALID_PRIORITIES:
            raise ValueError(f"Priority must be one of {VALID_PRIORITIES}")

        for k, v in update_dict.items():
            old_value = getattr(task, k, None)
            if str(old_value) != str(v):   # only log actual changes
                activity = TaskActivity(
                    task_uid=task.uid,
                    user_uid=user_uid,
                    action=f'{k}_changed',
                    old_value=str(old_value),
                    new_value=str(v)
                )
                session.add(activity)
            setattr(task, k, v)
            
        task.updated_at = datetime.now()
        
        await session.commit()
        await session.refresh(task)
        return task

    async def delete_task(self, task: Task, session: AsyncSession):
        """Delete a task."""
        await session.delete(task)
        await session.commit()
        
