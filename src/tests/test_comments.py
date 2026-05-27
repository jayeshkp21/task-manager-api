import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import Project, ProjectMember, Task, Comment
from datetime import datetime

TEST_USER_UID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def create_project_with_membership(session: AsyncSession):
    project = Project(
        uid=uuid.uuid4(), name="Comment Test Project",
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
        uid=uuid.uuid4(), title="Test Task for Comments",
        description="A task for comment testing",
        project_uid=project_uid,
        created_by=TEST_USER_UID,
        status="todo", priority="medium",
        created_at=datetime.now(), updated_at=datetime.now()
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def test_add_comment(client: AsyncClient, session: AsyncSession):
    project = await create_project_with_membership(session)
    task = await create_task_in_db(session, project.uid)

    response = await client.post(
        f"/comments/projects/{project.uid}/tasks/{task.uid}/comments",
        json={"content": "This is a test comment"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "This is a test comment"
    assert data["author_uid"] == str(TEST_USER_UID)
    assert data["task_uid"] == str(task.uid)


async def test_get_comments(client: AsyncClient, session: AsyncSession):
    project = await create_project_with_membership(session)
    task = await create_task_in_db(session, project.uid)

    # Add a comment first
    await client.post(
        f"/comments/projects/{project.uid}/tasks/{task.uid}/comments",
        json={"content": "First comment"}
    )
    await client.post(
        f"/comments/projects/{project.uid}/tasks/{task.uid}/comments",
        json={"content": "Second comment"}
    )

    response = await client.get(
        f"/comments/projects/{project.uid}/tasks/{task.uid}/comments"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["content"] == "First comment"
    assert data[1]["content"] == "Second comment"


async def test_delete_comment(client: AsyncClient, session: AsyncSession):
    project = await create_project_with_membership(session)
    task = await create_task_in_db(session, project.uid)

    response = await client.post(
        f"/comments/projects/{project.uid}/tasks/{task.uid}/comments",
        json={"content": "Comment to delete"}
    )
    comment_uid = response.json()["uid"]

    # Delete comment
    delete_response = await client.delete(
        f"/comments/projects/{project.uid}/tasks/{task.uid}/comments/{comment_uid}"
    )
    assert delete_response.status_code == 204

    # Fetch comments to confirm deletion
    get_response = await client.get(
        f"/comments/projects/{project.uid}/tasks/{task.uid}/comments"
    )
    assert len(get_response.json()) == 0


async def test_delete_nonexistent_comment(client: AsyncClient, session: AsyncSession):
    project = await create_project_with_membership(session)
    task = await create_task_in_db(session, project.uid)

    response = await client.delete(
        f"/comments/projects/{project.uid}/tasks/{task.uid}/comments/{uuid.uuid4()}"
    )
    assert response.status_code == 404
