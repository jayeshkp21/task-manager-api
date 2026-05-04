# Task Manager API

A production-ready REST API for managing projects and tasks, functioning as a lightweight Jira clone. Built with FastAPI, SQLModel (PostgreSQL), and Redis.

## Tech Stack
- **FastAPI**: Modern, fast web framework for building APIs.
- **SQLModel & PostgreSQL**: Database ORM and relational database.
- **Redis**: Token blocklist and caching.
- **JWT**: Stateless authentication with access and refresh tokens.

## Features
- **Authentication & RBAC**: Two-level role-based access control (System Roles + Project Roles).
- **Project Management**: Create projects, manage members, assign roles.
- **Task Tracking**: Assign tasks, track status/priority, pagination, filtering.
- **Activity Log**: Every task modification is automatically logged.
- **Comments**: Discussion threads on tasks.
- **Robust Error Handling**: Custom exception handlers with standardized JSON responses.

## Setup & Running Locally

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the root directory and configure the environment variables:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/taskmanager
   REDIS_URL=redis://localhost:6379/0
   SECRET_KEY=your_secret_key
   DOMAIN=localhost:8000
   ```

3. Run migrations and start the server:
   ```bash
   alembic upgrade head
   fastapi run src/__init__.py --port 8000
   ```

## Key Endpoints

| Method | Path | Auth Req | Description |
|--------|------|----------|-------------|
| POST | `/auth/signup` | No | Register a new user |
| POST | `/auth/login` | No | Login and get JWT |
| GET | `/projects/` | Admin | Get all projects in system |
| GET | `/projects/mine` | Yes | Get projects user is member of |
| POST | `/projects/` | Yes | Create a new project |
| GET | `/projects/{uid}/stats`| Yes | Get project task/member stats |
| GET | `/tasks/projects/{uid}/tasks`| Yes | Get paginated tasks with filters |
| GET | `/tasks/my-tasks`| Yes | Get all tasks assigned to me |
| POST | `/comments/projects/{p_uid}/tasks/{t_uid}/comments`| Yes | Add a comment to a task |

## Testing
Testing is configured with `pytest` using an in-memory SQLite database.
Run `pytest` to execute the test suite. (Tests to be added)

## Deployment
This project is configured to be deployed easily using Docker and a `docker-compose.yml` file. (Docker configs to be added)
