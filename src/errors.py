from typing import Any, Callable
from fastapi import FastAPI, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
 
class TaskManagerException(Exception):
    pass
 
class UserAlreadyExists(TaskManagerException): pass
class UserNotFound(TaskManagerException): pass
class InvalidCredentials(TaskManagerException): pass
class InvalidToken(TaskManagerException): pass
class AccountNotVerified(TaskManagerException): pass
class ProjectNotFound(TaskManagerException): pass
class TaskNotFound(TaskManagerException): pass
class NotProjectMember(TaskManagerException): pass
class InsufficientPermission(TaskManagerException): pass
class MemberNotFound(TaskManagerException): pass
 
def make_handler(status_code: int, detail: Any) -> Callable:
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content=detail)
    return handler
 
def register_all_errors(app: FastAPI):
    app.add_exception_handler(UserAlreadyExists,
        make_handler(403, {'message':'User with this email already exists','error_code':'user_exists'}))
    app.add_exception_handler(UserNotFound,
        make_handler(404, {'message':'User not found','error_code':'user_not_found'}))
    app.add_exception_handler(InvalidCredentials,
        make_handler(401, {'message':'Invalid email or password','error_code':'invalid_credentials'}))
    app.add_exception_handler(InvalidToken,
        make_handler(401, {'message':'Token is invalid or expired','error_code':'invalid_token'}))
    app.add_exception_handler(AccountNotVerified,
        make_handler(403, {'message':'Please verify your email','error_code':'account_not_verified'}))
    app.add_exception_handler(ProjectNotFound,
        make_handler(404, {'message':'Project not found','error_code':'project_not_found'}))
    app.add_exception_handler(TaskNotFound,
        make_handler(404, {'message':'Task not found','error_code':'task_not_found'}))
    app.add_exception_handler(NotProjectMember,
        make_handler(403, {'message':'You are not a member of this project','error_code':'not_member'}))
    app.add_exception_handler(InsufficientPermission,
        make_handler(403, {'message':'Insufficient project permissions','error_code':'insufficient_permission'}))
    app.add_exception_handler(MemberNotFound,
        make_handler(404, {'message':'Project member not found','error_code':'member_not_found'}))
 
    @app.exception_handler(500)
    async def server_error(request, exc):
        return JSONResponse(status_code=500,
            content={'message':'Internal server error','error_code':'server_error'})
 
    @app.exception_handler(SQLAlchemyError)
    async def db_error(request, exc):
        print(str(exc))  # log to terminal
        return JSONResponse(status_code=500, content={'message':'Database error','error_code':'db_error'})
    
