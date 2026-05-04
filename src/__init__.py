from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.db.main import initdb
from src.auth.routes import auth_router
from src.projects.routes import project_router
from src.tasks.routes import task_router
from src.comments.routes import comments_router
from src.errors import register_all_errors
from src.middleware import register_middleware
from src.errors import *

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server is starting...")
    await initdb()
    yield
    print("Server is stopping")

app = FastAPI(
    title="Task Manager API",
    description="A REST API for managing tasks, built with FastAPI and PostgreSQL.",
    lifespan=lifespan
)

register_all_errors(app)
register_middleware(app)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(project_router, prefix="/projects", tags=["Projects"])
app.include_router(task_router, prefix="/tasks", tags=["Tasks"])
app.include_router(comments_router, prefix="/comments", tags=["Comments"])