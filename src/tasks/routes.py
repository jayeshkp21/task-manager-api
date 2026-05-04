import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import RoleChecker, get_current_user
from src.db.main import get_session
from src.db.models import User, Task, TaskActivity
from src.projects.service import ProjectService
from .schemas import TaskCreateModel, TaskModel, TaskUpdateModel, PaginatedResponse
from .service import TaskService
from src.errors import *
from sqlmodel import select

task_router = APIRouter()
task_service = TaskService()
project_service = ProjectService()

verified_user = Depends(RoleChecker(["admin", "member"]))


async def get_task_or_404(task_uid: uuid.UUID, session: AsyncSession):
    task = await task_service.get_task(task_uid, session)
    if not task:
        raise TaskNotFound()
    return task


async def require_project_membership(
    project_uid: uuid.UUID, current_user: User, session: AsyncSession
):
    """Ensure user is a member of the project or is a system admin."""
    if current_user.role == "admin":
        return None  # system admin bypasses

    membership = await project_service.get_membership(project_uid, current_user.uid, session)
    if not membership:
        raise NotProjectMember()
    return membership


# ── GET ALL TASKS IN A PROJECT ──────────────────────────────────
@task_router.get(
    "/projects/{project_uid}/tasks",
    response_model=PaginatedResponse,
    dependencies=[verified_user]
)
async def get_project_tasks(
    project_uid: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    priority: Optional[str] = Query(default=None),
    assigned_to: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
):
    """
    Get all tasks in a project. Supports filtering:
    - ?status=todo
    - ?priority=high
    - ?assigned_to={user_uid}
    """
    # verify project exists
    project = await project_service.get_project(project_uid, session)
    if not project:
        raise ProjectNotFound()

    await require_project_membership(project_uid, current_user, session)

    tasks, total = await task_service.get_project_tasks(
        project_uid, session,
        status=status_filter,
        priority=priority,
        assigned_to=assigned_to,
        page=page,
        page_size=page_size
    )
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=tasks)


# ── GET SINGLE TASK ─────────────────────────────────────────────
@task_router.get(
    "/projects/{project_uid}/tasks/{task_uid}",
    response_model=TaskModel,
    dependencies=[verified_user]
)
async def get_task(
    project_uid: uuid.UUID,
    task_uid: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a single task. Must be a project member."""
    await require_project_membership(project_uid, current_user, session)
    task = await get_task_or_404(task_uid, session)
    return task


# ── CREATE TASK ─────────────────────────────────────────────────
@task_router.post(
    "/projects/{project_uid}/tasks",
    response_model=TaskModel,
    status_code=status.HTTP_201_CREATED,
    dependencies=[verified_user]
)
async def create_task(
    project_uid: uuid.UUID,
    task_data: TaskCreateModel,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a task in a project. Any project member can create tasks."""
    project = await project_service.get_project(project_uid, session)
    if not project:
        raise ProjectNotFound()

    await require_project_membership(project_uid, current_user, session)

    new_task = await task_service.create_task(
        task_data, project_uid, current_user.uid, session
    )
    return new_task


# ── UPDATE TASK ─────────────────────────────────────────────────
@task_router.patch(
    "/projects/{project_uid}/tasks/{task_uid}",
    response_model=TaskModel,
    dependencies=[verified_user]
)
async def update_task(
    project_uid: uuid.UUID,
    task_uid: uuid.UUID,
    update_data: TaskUpdateModel,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Update a task.
    - Project owner/admin can update anything.
    - Assigned user can only update the status field.
    - Other members cannot update.
    """
    membership = await require_project_membership(project_uid, current_user, session)
    task = await get_task_or_404(task_uid, session)

    # system admin can do anything
    if current_user.role == "admin":
        pass
    elif membership and membership.role in ["owner", "admin"]:
        pass  # project owner/admin can update anything
    elif str(task.assigned_to) == str(current_user.uid):
        # assigned user can only change status
        allowed_fields = set(update_data.model_dump(exclude_unset=True).keys())
        if allowed_fields - {"status"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Assigned users can only update the status field"
            )
    else:
        raise InsufficientPermission(detail="Only project owner/admin or assigned user can update this task")

    try:
        updated_task = await task_service.update_task(task, update_data, current_user.uid, session)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return updated_task


# ── DELETE TASK ─────────────────────────────────────────────────
@task_router.delete(
    "/projects/{project_uid}/tasks/{task_uid}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[verified_user]
)
async def delete_task(
    project_uid: uuid.UUID,
    task_uid: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a task. Project owner/admin or system admin only."""
    membership = await require_project_membership(project_uid, current_user, session)
    task = await get_task_or_404(task_uid, session)

    if current_user.role != "admin" and (not membership or membership.role not in ["owner", "admin"]):
        raise InsufficientPermission(detail="Only project owner/admin or system admin can delete this task")

    await task_service.delete_task(task, session)
    
@task_router.get('/projects/{project_uid}/tasks/{t_uid}/activity', dependencies=[verified_user])
async def get_task_activity(
    project_uid: uuid.UUID,
    t_uid: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get activity log for a task."""
    await require_project_membership(project_uid, current_user, session)
    task = await get_task_or_404(t_uid, session)
    
    statement = select(TaskActivity).where(TaskActivity.task_uid == task.uid)
    result = await session.execute(statement)
    return result.scalars().all()


# ── GET MY TASKS ────────────────────────────────────────────────
@task_router.get('/my-tasks', response_model=List[TaskModel], dependencies=[verified_user])
async def get_my_tasks(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    status_filter: Optional[str] = Query(default=None, alias='status'),
):
    """Get all tasks assigned to the current user across all projects."""
    statement = select(Task).where(Task.assigned_to == current_user.uid)
    if status_filter:
        statement = statement.where(Task.status == status_filter)
    result = await session.execute(statement)
    return result.scalars().all()