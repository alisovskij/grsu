from fastapi import Request, HTTPException

from src.api.routes.auth import SESSION_KEY
from src.models.user import User
from src.utils.database.session import SessionDep


async def get_current_user(
        request: Request,
        db: SessionDep
) -> User:

    user_id = request.session.get(SESSION_KEY)
    if not user_id:
        raise HTTPException(status_code=401, detail="Не авторизован")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return user