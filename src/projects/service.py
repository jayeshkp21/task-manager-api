import uuid
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import Project, ProjectMember, User
from .schemas import ProjectCreateModel, ProjectUpdateModel


class ProjectService:

    async def get_all_projects(self, session: AsyncSession, page: int = 1, page_size: int = 20):
        """Get all projects. Used by system admins only."""
        statement = select(Project).offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(statement)
        
        from sqlmodel import func
        count_statement = select(func.count()).select_from(Project)
        total = await session.scalar(count_statement)
        
        return result.scalars().all(), total

    async def get_user_projects(self, user_uid: uuid.UUID, session: AsyncSession, page: int = 1, page_size: int = 20):
        """Get all projects where the user is a member."""
        statement = (
            select(Project)
            .join(ProjectMember, Project.uid == ProjectMember.project_uid)
            .where(ProjectMember.user_uid == user_uid)
        ).offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(statement)
        
        from sqlmodel import func
        count_statement = (
            select(func.count()).select_from(Project)
            .join(ProjectMember, Project.uid == ProjectMember.project_uid)
            .where(ProjectMember.user_uid == user_uid)
        )
        total = await session.scalar(count_statement)
        
        return result.scalars().all(), total

    async def get_project(self, project_uid: uuid.UUID, session: AsyncSession):
        """Get a single project by uid."""
        statement = select(Project).where(Project.uid == project_uid)
        result = await session.execute(statement)
        return result.scalars().first()

    async def create_project(
        self, project_data: ProjectCreateModel, owner: User, session: AsyncSession
    ):
        """Create a project and automatically add the owner as a member with role 'owner'."""
        project_data_dict = project_data.model_dump()
        new_project = Project(**project_data_dict, owner_id=owner.uid)

        session.add(new_project)
        await session.flush()  # flush so new_project.uid is available

        # automatically add the creator as owner member
        owner_membership = ProjectMember(
            project_uid=new_project.uid,
            user_uid=owner.uid,
            role="owner"
        )
        session.add(owner_membership)
        await session.commit()
        await session.refresh(new_project)

        return new_project

    async def update_project(
        self, project: Project, update_data: ProjectUpdateModel, session: AsyncSession
    ):
        """Update project fields. Only non-None values are updated."""
        update_dict = update_data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(project, k, v)
        await session.commit()
        await session.refresh(project)
        return project

    async def delete_project(self, project: Project, session: AsyncSession):
        """Delete a project and all its members and tasks (cascade)."""
        await session.delete(project)
        await session.commit()

    async def get_membership(
        self, project_uid: uuid.UUID, user_uid: uuid.UUID, session: AsyncSession
    ):
        """Check if a user is a member of a project and return the membership."""
        statement = (
            select(ProjectMember)
            .where(ProjectMember.project_uid == project_uid)
            .where(ProjectMember.user_uid == user_uid)
        )
        result = await session.execute(statement)
        return result.scalars().first()

    async def add_member(
        self, project_uid: uuid.UUID, user_uid: uuid.UUID, role: str, session: AsyncSession
    ):
        """Add a user to a project."""
        new_member = ProjectMember(
            project_uid=project_uid,
            user_uid=user_uid,
            role=role
        )
        session.add(new_member)
        await session.commit()
        await session.refresh(new_member)
        return new_member

    async def remove_member(self, membership: ProjectMember, session: AsyncSession):
        """Remove a user from a project."""
        await session.delete(membership)
        await session.commit()

    async def update_member_role(
        self, membership: ProjectMember, new_role: str, session: AsyncSession
    ):
        """Change a member's project role."""
        membership.role = new_role
        await session.commit()
        await session.refresh(membership)
        return membership

    async def get_project_members(self, project_uid: uuid.UUID, session: AsyncSession, page: int = 1, page_size: int = 20):
        """Get all members of a project."""
        statement = select(ProjectMember).where(ProjectMember.project_uid == project_uid).offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(statement)
        
        from sqlmodel import func
        count_statement = select(func.count()).select_from(ProjectMember).where(ProjectMember.project_uid == project_uid)
        total = await session.scalar(count_statement)
        
        return result.scalars().all(), total
    
    