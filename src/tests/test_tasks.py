import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import Project, ProjectMember, Task
from datetime import datetime


TEST_USER_UID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def create_project_with_membership(session: AsyncSession):
    project = Project(
        uid=uuid.uuid4(), name="Task Test Project",
        owner_id=TEST_USER_UID, status="active",
        created_at=datetime.now(), updated_at=datetime.now()
    )
    session.add(project)
    await session.flush()
    membership = ProjectMember(
        uid=uuid.uuid4(), project_uid=project.uid,
        user_uid=TEST_USER_UID, role="owner",
        joined_at=datetime.now()
    )
    session.add(membership)
    await session.commit()
    await session.refresh(project)
    return project


async def create_task_in_db(session: AsyncSession, project_uid: uuid.UUID):
    task = Task(
        uid=uuid.uuid4(), title="Test Task",
        description="A task for testing",
        project_uid=project_uid,
        created_by=TEST_USER_UID,
        status="todo", priority="medium",
        created_at=datetime.now(), updated_at=datetime.now()
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def test_create_task(client: AsyncClient, session: AsyncSession):
    project = await create_project_with_membership(session)
    response = await client.post(
        f"/tasks/projects/{project.uid}/tasks",
        json={"title": "New Task", "priority": "high"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Task"
    assert data["status"] == "todo"  # always starts as todo
    assert data["priority"] == "high"


async def test_create_task_invalid_priority(client: AsyncClient, session: AsyncSession):
    project = await create_project_with_membership(session)
    response = await client.post(
        f"/tasks/projects/{project.uid}/tasks",
        json={"title": "Bad Priority Task", "priority": "urgent"}  # invalid
    )
    assert response.status_code == 422


async def test_get_project_tasks(client: AsyncClient, session: AsyncSession):
    project = await create_project_with_membership(session)
    await create_task_in_db(session, project.uid)
    response = await client.get(f"/tasks/projects/{project.uid}/tasks")
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)
    assert len(response.json()["items"]) >= 1


async def test_filter_tasks_by_status(client: AsyncClient, session: AsyncSession):
    project = await create_project_with_membership(session)
    await create_task_in_db(session, project.uid)
    response = await client.get(
        f"/tasks/projects/{project.uid}/tasks?status=todo"
    )
    assert response.status_code == 200
    for task in response.json()["items"]:
        assert task["status"] == "todo"


async def test_update_task_status(client: AsyncClient, session: AsyncSession):
    project = await create_project_with_membership(session)
    task = await create_task_in_db(session, project.uid)
    response = await client.patch(
        f"/tasks/projects/{project.uid}/tasks/{task.uid}",
        json={"status": "in_progress"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


async def test_update_task_invalid_status(client: AsyncClient, session: AsyncSession):
    project = await create_project_with_membership(session)
    task = await create_task_in_db(session, project.uid)
    response = await client.patch(
        f"/tasks/projects/{project.uid}/tasks/{task.uid}",
        json={"status": "banana"}  # invalid
    )
    assert response.status_code == 400


async def test_delete_task(client: AsyncClient, session: AsyncSession):
    project = await create_project_with_membership(session)
    task = await create_task_in_db(session, project.uid)
    response = await client.delete(
        f"/tasks/projects/{project.uid}/tasks/{task.uid}"
    )
    assert response.status_code == 204

    # Confirm gone
    response = await client.get(
        f"/tasks/projects/{project.uid}/tasks/{task.uid}"
    )
    assert response.status_code == 404


async def test_get_nonexistent_task(client: AsyncClient, session: AsyncSession):
    project = await create_project_with_membership(session)
    response = await client.get(
        f"/tasks/projects/{project.uid}/tasks/{uuid.uuid4()}"
    )
    assert response.status_code == 404


async def test_task_activity_logged(client: AsyncClient, session: AsyncSession):
    project = await create_project_with_membership(session)
    task = await create_task_in_db(session, project.uid)

    # Update status to log an activity
    update_response = await client.patch(
        f"/tasks/projects/{project.uid}/tasks/{task.uid}",
        json={"status": "in_progress"}
    )
    assert update_response.status_code == 200

    # Get task activity log
    activity_response = await client.get(
        f"/tasks/projects/{project.uid}/tasks/{task.uid}/activity"
    )
    assert activity_response.status_code == 200
    activities = activity_response.json()
    assert len(activities) >= 1
    assert activities[0]["action"] == "status_changed"
    assert activities[0]["old_value"] == "todo"
    assert activities[0]["new_value"] == "in_progress"