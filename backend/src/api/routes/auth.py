from fastapi import APIRouter, HTTPException, Request, Depends

from src.core.security import hash_password, verify_password, SESSION_KEY
from src.dependencies.user import get_current_user
from src.models.user import User
from src.schemas.user import UserSchema, UserLoginSchema
from src.services.auth_user import get_user_by_email
from src.services.find_teacher_in_grsu import find_teacher_in_grsu
from src.utils.database.session import SessionDep

router = APIRouter()

@router.post("/login")
async def login_user(
    user: UserLoginSchema,
    db: SessionDep,
    request: Request
):
    existing_user = await get_user_by_email(db, user.email)

    if existing_user and verify_password(user.password, existing_user.password):
        request.session[SESSION_KEY] = existing_user.id
        return {"message": "Вы успешно авторизованы"}

    if not existing_user:
        grsu_user_data = find_teacher_in_grsu(user.email)
        if grsu_user_data and user.password == grsu_user_data['id']:
            new_user = User(
                username=f"{grsu_user_data['surname']} {grsu_user_data['name']} {grsu_user_data['patronym']}",
                email=grsu_user_data['email'],
                password=hash_password(grsu_user_data['id']),
                post=grsu_user_data['post'],
                schedule_id=grsu_user_data['id'],
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            request.session[SESSION_KEY] = new_user.id
            return UserSchema.from_orm(new_user)

    raise HTTPException(status_code=401, detail="Неверный email или пароль")


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return UserSchema.from_orm(current_user)


@router.post("/logout")
async def logout(request: Request):
    request.session.pop(SESSION_KEY, None)
    return {"message": "Вы вышли из системы"}


@router.get('/check_session')
def check_session(request: Request):
    user_id = request.session.get(SESSION_KEY)

    if user_id:
        return {"active": True}

    return {"active": False}


