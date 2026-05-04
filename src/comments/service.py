import uuid
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import Comment

class CommentService:
    async def get_task_comments(self, task_uid: uuid.UUID, session: AsyncSession):
        statement = select(Comment).where(Comment.task_uid == task_uid).order_by(Comment.created_at)
        result = await session.execute(statement)
        return result.scalars().all()

    async def get_comment(self, comment_uid: uuid.UUID, session: AsyncSession):
        statement = select(Comment).where(Comment.uid == comment_uid)
        result = await session.execute(statement)
        return result.scalars().first()

    async def create_comment(self, task_uid: uuid.UUID, author_uid: uuid.UUID, content: str, session: AsyncSession):
        comment = Comment(
            task_uid=task_uid,
            author_uid=author_uid,
            content=content
        )
        session.add(comment)
        await session.commit()
        await session.refresh(comment)
        return comment

    async def delete_comment(self, comment: Comment, session: AsyncSession):
        await session.delete(comment)
        await session.commit()
