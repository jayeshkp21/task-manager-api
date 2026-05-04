from typing import List
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from src.auth.utils import decode_token
from src.db.main import get_session
from src.db.redis import token_in_blocklist
from .service import UserService
from sqlalchemy.ext.asyncio import AsyncSession
from src.errors import *

user_service = UserService()

class TokenBearer(HTTPBearer):
    def __init__(self, auto_error=True):
        super().__init__(auto_error=auto_error)
        
    async def __call__(self, request: Request):
        creds = await super().__call__(request)
        
        token = creds.credentials
        token_data = decode_token(token)
        
        if not self.token_valid(token):
            raise InvalidToken()
        
        if await token_in_blocklist(token_data.get('jti')):
            raise InvalidToken(detail="Token has been revoked, please login again")
        
        
        self.verify_token_data(token_data)
        
        return token_data
    
    def token_valid(self, token: str) ->bool:
        token_data = decode_token(token)
        
        return True if token_data is not None else False
    
    def verify_token_data(self, token_data):
        raise NotImplementedError("Please override this method in child classes")
    
class AccessTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict):
        if token_data and token_data.get('refresh'):
            raise InvalidToken(detail="Please provide an access token")
        
class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict):
        if token_data and not token_data.get('refresh'):
            raise InvalidToken(detail="Please provide a refresh token")
        
async def get_current_user(token_details:dict = Depends(AccessTokenBearer()), session: AsyncSession = Depends(get_session)):
    user_email = token_details['user']['email']
    
    user = await user_service.get_user_by_email(user_email, session)
    
    return user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = allowed_roles
        
    def __call__(self, current_user = Depends(get_current_user)) ->any:
        if not current_user.is_verified:
            raise AccountNotVerified()
        if current_user.role in self.allowed_roles:
            return True
        
        raise InsufficientPermission()