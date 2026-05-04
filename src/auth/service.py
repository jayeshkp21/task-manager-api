from sqlmodel import select
from .schemas import UserCreateModel
from src.db.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from .utils import generate_password_hash

class UserService:
    async def get_user_by_email(self, email: str, session: AsyncSession) -> User:
        statement = select(User).where(User.email == email)
        result = await session.execute(statement)
        user = result.scalars().first()
        return user
    
    async def user_exists(self, email: str, session: AsyncSession) -> bool:
        user = await self.get_user_by_email(email, session)
        
        return True if user is not None else False
    
    async def create_user(self, user_data: UserCreateModel, session: AsyncSession):
        password_hash = generate_password_hash(user_data.password)
        user_data_dict = user_data.model_dump(exclude={'password'})
        
        new_user = User(**user_data_dict, password_hash=password_hash)
        
        session.add(new_user)
        await session.commit()
        
        return new_user
    
    async def update_user(self, user: User, user_data: dict, session: AsyncSession):
        
        for k, v in user_data.items():
            setattr(user, k, v)
            
        await session.commit()
        
        return user
        