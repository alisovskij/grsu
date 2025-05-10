from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from src.core.security import hash_password, verify_password
from src.models.user import User
from src.schemas.user import UserSchema, UserLoginSchema
from src.services.find_teacher_in_grsu import find_teacher_in_grsu
from src.utils.database.session import SessionDep

router = APIRouter()

SESSION_KEY = "user_id"

@router.post("/login")
async def login_user(
    user: UserLoginSchema,
    db: SessionDep,
    request: Request
):
    user_find = (
        await db.execute(
            select(User).where(User.email == user.email)
        )
    ).scalar_one_or_none()

    if user_find and verify_password(user.password, user_find.password):
        request.session[SESSION_KEY] = user_find.id
        return {"message": "Вы успешно авторизованы"}

    if not user_find:
        user_in_grsu = find_teacher_in_grsu(user.email)
        if user_in_grsu and user.password == user_in_grsu['id']:
            new_user = User(
                username=f"{user_in_grsu['surname']} {user_in_grsu['name']} {user_in_grsu['patronym']}",
                email=user_in_grsu['email'],
                password=hash_password(user_in_grsu['id']),
                post=user_in_grsu['post'],
                schedule_id=user_in_grsu['id'],
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            request.session[SESSION_KEY] = new_user.id
            return UserSchema.from_orm(new_user)

    raise HTTPException(status_code=401, detail="Неверный email или пароль")


@router.get("/me")
async def get_me(request: Request, db: SessionDep):
    user_id = request.session.get(SESSION_KEY)
    if not user_id:
        raise HTTPException(status_code=401, detail="Не авторизован")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return UserSchema.from_orm(user)


@router.post("/logout")
async def logout(request: Request):
    request.session.pop(SESSION_KEY, None)
    return {"message": "Вы вышли из системы"}
