import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.auth.dependencies import RoleChecker, get_current_user
from src.db.main import get_session
from src.db.models import User, Task, ProjectMember
from src.auth.service import UserService
from .schemas import (
    AddMemberModel, ProjectCreateModel, ProjectDetailModel,
    ProjectModel, ProjectUpdateModel, UpdateMemberRoleModel, MemberModel, PaginatedResponse
)
from .service import ProjectService
from typing import List
from src.errors import *

project_router = APIRouter()
project_service = ProjectService()
user_service = UserService()

# Role checkers
verified_user = Depends(RoleChecker(["admin", "member"]))
admin_only = Depends(RoleChecker(["admin"]))


async def get_project_or_404(project_uid: uuid.UUID, session: AsyncSession = Depends(get_session)):
    """Reusable dependency — fetches project or raises 404."""
    project = await project_service.get_project(project_uid, session)
    if not project:
        raise ProjectNotFound()
    return project


async def require_project_role(
    required_roles: list,
    project_uid: uuid.UUID,
    current_user: User,
    session: AsyncSession
):
    """
    Check if the current user has a required project-level role.
    System admins bypass this check entirely.
    """
    if current_user.role == "admin":
        return  # system admin can do anything

    membership = await project_service.get_membership(project_uid, current_user.uid, session)
    if not membership:
        raise NotProjectMember()
    if membership.role not in required_roles:
        raise InsufficientPermission(detail=f"This action requires one of these roles: {required_roles}")


# ── GET ALL PROJECTS (admin only) ──────────────────────────────
@project_router.get("/", response_model=PaginatedResponse, dependencies=[admin_only])
async def get_all_projects(
    session: AsyncSession = Depends(get_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
):
    """System admin: get every project in the system."""
    projects, total = await project_service.get_all_projects(session, page, page_size)
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=projects)


# ── GET MY PROJECTS ─────────────────────────────────────────────
@project_router.get("/mine", response_model=PaginatedResponse, dependencies=[verified_user])
async def get_my_projects(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
):
    """Get all projects the current user is a member of."""
    projects, total = await project_service.get_user_projects(current_user.uid, session, page, page_size)
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=projects)


# ── GET SINGLE PROJECT ──────────────────────────────────────────
@project_router.get("/{project_uid}", response_model=ProjectDetailModel, dependencies=[verified_user])
async def get_project(
    project_uid: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a single project with its members. Must be a member or admin."""
    project = await get_project_or_404(project_uid, session)
    await require_project_role(
        ["owner", "admin", "member"], project_uid, current_user, session
    )
    return project


# ── CREATE PROJECT ──────────────────────────────────────────────
@project_router.post("/", response_model=ProjectModel, status_code=status.HTTP_201_CREATED, dependencies=[verified_user])
async def create_project(
    project_data: ProjectCreateModel,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new project. Creator becomes owner automatically."""
    new_project = await project_service.create_project(project_data, current_user, session)
    return new_project


# ── UPDATE PROJECT ──────────────────────────────────────────────
@project_router.patch("/{project_uid}", response_model=ProjectModel, dependencies=[verified_user])
async def update_project(
    project_uid: uuid.UUID,
    update_data: ProjectUpdateModel,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update project details. Owner or project admin only."""
    project = await get_project_or_404(project_uid, session)
    await require_project_role(["owner", "admin"], project_uid, current_user, session)
    updated = await project_service.update_project(project, update_data, session)
    return updated


# ── DELETE PROJECT ──────────────────────────────────────────────
@project_router.delete("/{project_uid}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[verified_user])
async def delete_project(
    project_uid: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a project. Owner or system admin only."""
    project = await get_project_or_404(project_uid, session)
    await require_project_role(["owner"], project_uid, current_user, session)
    await project_service.delete_project(project, session)


# ── GET PROJECT MEMBERS ─────────────────────────────────────────
@project_router.get("/{project_uid}/members", response_model=PaginatedResponse, dependencies=[verified_user])
async def get_project_members(
    project_uid: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
):
    """Get all members of a project."""
    await get_project_or_404(project_uid, session)
    await require_project_role(
        ["owner", "admin", "member"], project_uid, current_user, session
    )
    members, total = await project_service.get_project_members(project_uid, session, page, page_size)
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=members)


# ── ADD MEMBER ──────────────────────────────────────────────────
@project_router.post("/{project_uid}/members", response_model=MemberModel, status_code=status.HTTP_201_CREATED, dependencies=[verified_user])
async def add_member(
    project_uid: uuid.UUID,
    member_data: AddMemberModel,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Add a user to the project. Owner or project admin only."""
    await get_project_or_404(project_uid, session)
    await require_project_role(["owner", "admin"], project_uid, current_user, session)

    # check user to add actually exists
    statement = select(User).where(User.uid == member_data.user_uid)
    result = await session.execute(statement)
    user_to_add = result.scalars().first()
    if not user_to_add:
        raise UserNotFound()

    # check not already a member
    existing = await project_service.get_membership(project_uid, member_data.user_uid, session)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member")

    new_member = await project_service.add_member(
        project_uid, member_data.user_uid, member_data.role, session
    )
    return new_member


# ── REMOVE MEMBER ───────────────────────────────────────────────
@project_router.delete("/{project_uid}/members/{user_uid}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[verified_user])
async def remove_member(
    project_uid: uuid.UUID,
    user_uid: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Remove a member from the project. Owner only."""
    await get_project_or_404(project_uid, session)
    await require_project_role(["owner"], project_uid, current_user, session)

    membership = await project_service.get_membership(project_uid, user_uid, session)
    if not membership:
        raise MemberNotFound()

    await project_service.remove_member(membership, session)


# ── UPDATE MEMBER ROLE ──────────────────────────────────────────
@project_router.patch("/{project_uid}/members/{user_uid}", response_model=MemberModel, dependencies=[verified_user])
async def update_member_role(
    project_uid: uuid.UUID,
    user_uid: uuid.UUID,
    role_data: UpdateMemberRoleModel,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Change a member's project role. Owner only."""
    await get_project_or_404(project_uid, session)
    await require_project_role(["owner"], project_uid, current_user, session)

    membership = await project_service.get_membership(project_uid, user_uid, session)
    if not membership:
        raise MemberNotFound()

    updated = await project_service.update_member_role(membership, role_data.role, session)
    return updated


# ── GET PROJECT STATS ───────────────────────────────────────────
@project_router.get('/{project_uid}/stats', dependencies=[verified_user])
async def get_project_stats(
    project_uid: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get statistics for a project."""
    await require_project_role(['owner','admin','member'], project_uid, current_user, session)
 
    from sqlalchemy import func
    
    result = await session.execute(
        select(Task.status, func.count(Task.uid))
        .where(Task.project_uid == project_uid)
        .group_by(Task.status)
    )
    status_counts = dict(result.all())
 
    member_count = await session.scalar(
        select(func.count()).where(ProjectMember.project_uid == project_uid)
    )
 
    return {
        'total_tasks': sum(status_counts.values()),
        'by_status': status_counts,
        'total_members': member_count
    }