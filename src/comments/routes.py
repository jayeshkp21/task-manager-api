import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.main import get_session
from src.db.models import User
from src.auth.dependencies import RoleChecker, get_current_user
from src.tasks.service import TaskService
from src.projects.service import ProjectService
from src.errors import TaskNotFound, ProjectNotFound, NotProjectMember, InsufficientPermission
from .schemas import CommentModel, CommentCreateModel
from .service import CommentService

comments_router = APIRouter()
comment_service = CommentService()
task_service = TaskService()
project_service = ProjectService()

verified_user = Depends(RoleChecker(["admin", "member"]))

async def require_project_membership(project_uid: uuid.UUID, current_user: User, session: AsyncSession):
    if current_user.role == "admin":
        return None
    membership = await project_service.get_membership(project_uid, current_user.uid, session)
    if not membership:
        raise NotProjectMember()
    return membership

@comments_router.post('/projects/{project_uid}/tasks/{task_uid}/comments', response_model=CommentModel, status_code=status.HTTP_201_CREATED, dependencies=[verified_user])
async def add_comment(
    project_uid: uuid.UUID,
    task_uid: uuid.UUID,
    comment_data: CommentCreateModel,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    await require_project_membership(project_uid, current_user, session)
    task = await task_service.get_task(task_uid, session)
    if not task:
        raise TaskNotFound()
        
    return await comment_service.create_comment(task.uid, current_user.uid, comment_data.content, session)

@comments_router.get('/projects/{project_uid}/tasks/{task_uid}/comments', response_model=List[CommentModel], dependencies=[verified_user])
async def get_comments(
    project_uid: uuid.UUID,
    task_uid: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    await require_project_membership(project_uid, current_user, session)
    task = await task_service.get_task(task_uid, session)
    if not task:
        raise TaskNotFound()
        
    return await comment_service.get_task_comments(task.uid, session)

@comments_router.delete('/projects/{project_uid}/tasks/{task_uid}/comments/{comment_uid}', status_code=status.HTTP_204_NO_CONTENT, dependencies=[verified_user])
async def delete_comment(
    project_uid: uuid.UUID,
    task_uid: uuid.UUID,
    comment_uid: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    await require_project_membership(project_uid, current_user, session)
    task = await task_service.get_task(task_uid, session)
    if not task:
        raise TaskNotFound()
        
    comment = await comment_service.get_comment(comment_uid, session)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
        
    if str(comment.author_uid) != str(current_user.uid) and current_user.role != 'admin':
        raise InsufficientPermission(detail="You can only delete your own comments")
        
    await comment_service.delete_comment(comment, session)
