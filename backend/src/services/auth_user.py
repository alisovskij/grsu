from src.models.user import User
from src.utils.database.session import SessionDep
from sqlalchemy import select


async def get_user_by_email(
        db: SessionDep,
        email: str
) -> User:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

