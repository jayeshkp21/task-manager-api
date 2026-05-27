import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import Project, ProjectMember, User
from datetime import datetime
from src.auth.utils import generate_password_hash

async def create_project_in_db(session: AsyncSession, owner_uid: uuid.UUID, name="Test Project"):
    """Create a project directly in the test DB."""
    project = Project(
        uid=uuid.uuid4(),
        name=name,
        description="A test project",
        owner_id=owner_uid,
        status="active",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    session.add(project)
    await session.flush()

    membership = ProjectMember(
        uid=uuid.uuid4(),
        project_uid=project.uid,
        user_uid=owner_uid,
        role="owner",
        joined_at=datetime.now(),
    )
    session.add(membership)
    await session.commit()
    await session.refresh(project)
    return project


# The test user uid must match what override_get_current_user returns in conftest
TEST_USER_UID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def test_create_project(client: AsyncClient):
    '''Test that creating a project with valid data succeeds and returns the correct information.'''
    response = await client.post("/projects/", json={
        "name": "My Project",
        "description": "Test description"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Project"
    assert data["status"] == "active"


async def test_create_project_missing_name(client: AsyncClient):
    response = await client.post("/projects/", json={
        "description": "No name provided"
    })
    assert response.status_code == 422  # validation error


async def test_get_my_projects(client: AsyncClient, session: AsyncSession):
    await create_project_in_db(session, TEST_USER_UID, name="My Listed Project")
    response = await client.get("/projects/mine")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)
    assert any(p["name"] == "My Listed Project" for p in data["items"])


async def test_get_project_by_uid(client: AsyncClient, session: AsyncSession):
    project = await create_project_in_db(session, TEST_USER_UID, name="Detail Project")
    response = await client.get(f"/projects/{project.uid}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Detail Project"


async def test_update_project(client: AsyncClient, session: AsyncSession):
    project = await create_project_in_db(session, TEST_USER_UID, name="Old Name")
    response = await client.patch(f"/projects/{project.uid}", json={
        "name": "New Name"
    })
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


async def test_delete_project(client: AsyncClient, session: AsyncSession):
    project = await create_project_in_db(session, TEST_USER_UID, name="To Delete")
    response = await client.delete(f"/projects/{project.uid}")
    assert response.status_code == 204

    # Confirm it's gone
    response = await client.get(f"/projects/{project.uid}")
    assert response.status_code == 404


async def test_get_nonexistent_project(client: AsyncClient):
    response = await client.get(f"/projects/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_create_project_owner_becomes_member(client: AsyncClient, session: AsyncSession):
    response = await client.post("/projects/", json={"name": "Owner Check"})
    assert response.status_code == 201
    project_uid = response.json()["uid"]

    members_response = await client.get(f"/projects/{project_uid}/members")
    assert members_response.status_code == 200
    members = members_response.json()
    assert len(members["items"]) == 1
    assert members["items"][0]["role"] == "owner"
    assert members["items"][0]["user_uid"] == str(TEST_USER_UID)


async def test_add_project_member(client: AsyncClient, session: AsyncSession):
    project = await create_project_in_db(session, TEST_USER_UID, name="Member Test Project")
    
    # Create another user in DB
    new_user_uid = uuid.uuid4()
    from src.db.models import User
    new_user = User(
        uid=new_user_uid,
        username="newmember",
        email="newmember@example.com",
        first_name="New",
        last_name="Member",
        password_hash="hashed",
        role="member",
        is_verified=True,
    )
    session.add(new_user)
    await session.commit()

    # Add member to project
    response = await client.post(
        f"/projects/{project.uid}/members",
        json={"user_uid": str(new_user_uid), "role": "member"}
    )
    assert response.status_code == 201
    assert response.json()["user_uid"] == str(new_user_uid)
    assert response.json()["role"] == "member"


async def test_get_project_stats(client: AsyncClient, session: AsyncSession):
    project = await create_project_in_db(session, TEST_USER_UID, name="Stats Project")
    
    # Add a task to this project
    from src.db.models import Task
    task = Task(
        uid=uuid.uuid4(),
        title="Stats Task",
        project_uid=project.uid,
        created_by=TEST_USER_UID,
        status="todo",
        priority="medium"
    )
    session.add(task)
    await session.commit()

    response = await client.get(f"/projects/{project.uid}/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_tasks"] == 1
    assert data["by_status"]["todo"] == 1
    assert data["total_members"] == 1