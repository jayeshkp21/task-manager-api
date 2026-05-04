from datetime import timedelta, datetime
from fastapi import APIRouter, Depends,status
from sqlmodel import select
# from src import mail
from src.auth.dependencies import AccessTokenBearer, RefreshTokenBearer, RoleChecker, get_current_user
from src.config import Config
from src.db.redis import add_jti_to_blocklist
from src.mail import create_message, mail
from .schemas import PasswordResetConfirmModel, UserCreateModel, UserLoginModel, UserProjectsModel, EmailModel, PasswordResetModel
from sqlalchemy.ext.asyncio import AsyncSession
from .service import UserService
from src.db.main import get_session
from fastapi.exceptions import HTTPException
from .utils import create_access_token, generate_password_hash, verify_password, create_url_safe_token, decode_url_safe_token
from fastapi.responses import JSONResponse
from src.projects.routes import verified_user
from src.db.models import User
from src.errors import *

auth_router = APIRouter()

user_service = UserService()
role_checker = RoleChecker(allowed_roles=['admin', 'member', 'owner', 'user'])

@auth_router.post("/send_email")
async def send_email(emails: EmailModel):
    emails = emails.addresses

    html = "<h1>Welcome to the app</h1>"
    # subject = "Welcome to our app"
    message = create_message(
        recipients=emails,
        subject="Welcome to our app",
        body=html
    )
    
    await mail.send_message(message)

    # send_email.delay(emails, subject, html)

    return {"message": "Email sent successfully"}

@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreateModel, session: AsyncSession = Depends(get_session)):
    email = user_data.email
    
    user_exists = await user_service.user_exists(email, session)
    
    if user_exists:
        raise UserAlreadyExists()
    
    new_user = await user_service.create_user(user_data, session)
    
    token = create_url_safe_token({"email": email})
    
    link = f"http://{Config.DOMAIN}/auth/verify/{token}"

    html = f"""
    <h1>Verify your Email</h1>
    <p>Please click this <a href="{link}">link</a> to verify your email</p>
    """
    
    message = create_message(
        recipients=[email],
        subject="Verify your email",
        body=html
    )
    
    await mail.send_message(message)
    
    return {
        "message": "Account Created! Check email to verify your account",
        "user": new_user,
    }
    
@auth_router.get("/verify/{token}")
async def verify_user_account(token:str, session: AsyncSession = Depends(get_session)):
    token_data = decode_url_safe_token(token)
    
    user_email = token_data.get('email')
    
    if user_email:
        user = await user_service.get_user_by_email(user_email, session)
        
        if not user:
            raise UserNotFound()
        
        await user_service.update_user(user, {"is_verified": True}, session)
        
        return JSONResponse(content={'message':'Account Verified Successfully'}, status_code=status.HTTP_200_OK)
    
    return JSONResponse(
        content={"message": "Error occured during verification"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    
@auth_router.post("/login")
async def login_user(login_data: UserLoginModel, session: AsyncSession = Depends(get_session)):
    email = login_data.email
    password = login_data.password
    
    user = await user_service.get_user_by_email(email, session)
    
    if user is None:
        raise InvalidCredentials()
        
    if not user.is_verified:
        raise AccountNotVerified()
        
    password_valid = verify_password(password, user.password_hash)
    if not password_valid:
        raise InvalidCredentials()
        
    access_token = create_access_token(
        user_data={
            'email':user.email,
            'user_uid':str(user.uid),
            'role':user.role
        }
    )
    
    refresh_token = create_access_token(
        user_data={
            "email": user.email,
            "user_uid": str(user.uid),
            'role':user.role
        },
        refresh=True,
        expiry=timedelta(days=2),
    )
    
    return JSONResponse(
        content={
            'message':'Login successful',
            'access_token':access_token,
            'refresh_token':refresh_token,
            'user':{
                'email':user.email,
                'uid':str(user.uid),
                'role':user.role
            } 
        }
    )


@auth_router.get('/refresh_token')
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    expiry_timestamp = token_details.get('exp')
    
    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = create_access_token(
            user_data=token_details.get('user')
        )
        return JSONResponse(content={
            "access_token": new_access_token
        })
        
    raise InvalidToken()

@auth_router.get('/me', response_model=UserProjectsModel, dependencies=[verified_user])
async def get_current_user(user = Depends(get_current_user), _:bool = Depends(role_checker)):
    return user   

@auth_router.get('/logout')
async def revoke_token(token_details:dict = Depends(AccessTokenBearer())):
    jti = token_details.get('jti')
    
    await add_jti_to_blocklist(jti)
    
    return JSONResponse(
        content={'message':'Logged Out Successfully'},
        status_code=status.HTTP_200_OK
    )
    
@auth_router.post('/password_reset')
async def password_reset_request(email_data: PasswordResetModel, session: AsyncSession = Depends(get_session)):
    email = email_data.email
    
    token = create_url_safe_token({"email": email})

    link = f"http://{Config.DOMAIN}/auth/password-reset-confirm/{token}"

    html_message = f"""
    <h1>Reset Your Password</h1>
    <p>Please click this <a href="{link}">link</a> to Reset Your Password</p>
    """
    
    message = create_message(
        recipients=[email],
        subject="Reset your password",
        body=html_message
    )
    
    await mail.send_message(message)
    
    return JSONResponse(
        content={
            "message": "Please check your email for instructions to reset your password",
        },
        status_code=status.HTTP_200_OK,
    )

@auth_router.post("/password-reset-confirm/{token}")
async def reset_account_password(
    token: str,
    passwords: PasswordResetConfirmModel,
    session: AsyncSession = Depends(get_session),
):
    new_password = passwords.new_password
    confirm_password = passwords.confirm_new_password

    if new_password != confirm_password:
        raise InvalidCredentials(detail="Passwords do not match")

    token_data = decode_url_safe_token(token)

    user_email = token_data.get("email")

    if user_email:
        user = await user_service.get_user_by_email(user_email, session)

        if not user:
            raise UserNotFound()
        
        passwd_hash = generate_password_hash(new_password)
        await user_service.update_user(user, {"password_hash": passwd_hash}, session)

        return JSONResponse(
            content={"message": "Password reset Successfully"},
            status_code=status.HTTP_200_OK,
        )

    return JSONResponse(
        content={"message": "Error occured during password reset."},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    
@auth_router.get("/users/search")
async def search_users(
    q: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),  # just require login
):
    from sqlmodel import or_
    statement = select(User).where(
        or_(
            User.email.ilike(f"%{q}%"),
            User.username.ilike(f"%{q}%")
        )
    ).limit(10)
    result = await session.execute(statement)
    users = result.scalars().all()
    return [
        {
            "uid": str(u.uid),
            "username": u.username,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name
        }
        for u in users
    ]