from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, Query
import requests
from sqlalchemy import select

from src.models.grsu import Lesson, Group, LessonGroup
from src.models.user import User
from src.utils.database.session import SessionDep


router = APIRouter()

SESSION_KEY = "user_id"


@router.get('/schedule')
async def get_teacher_schedule(
        db: SessionDep,
        request: Request,
        dateStart: str,
        dateEnd: str
):
    user_id = request.session.get(SESSION_KEY)
    user = (
        await db.execute(
            select(User).where(User.id == user_id)
        )
    ).scalar_one_or_none()
    if not user_id:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    schedule = requests.get(
        f'http://api.grsu.by/1.x/app2/getTeacherSchedule?teacherId={user.schedule_id}&dateStart={dateStart}&dateEnd={dateEnd}'
    )

    return schedule.json()


@router.get('/getGroups')
async def get_teacher_schedule(
        db: SessionDep,
        request: Request,
        departmentId: int,
        facultyId: int,
        course: int
):
    user_id = request.session.get(SESSION_KEY)
    if not user_id:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    groups = requests.get(
        f'http://api.grsu.by/1.x/app2/getGroups?departmentId={departmentId}&facultyId={facultyId}&course={course}&lang=en_GB'
    )

    return groups.json()


@router.get('/students')
def get_student_by_id(
        request: Request,
        student_id: int
):
    user_id = request.session.get(SESSION_KEY)
    if not user_id:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    student = requests.get(
        f'http://api.grsu.by/1.x/app2/getStudent?login={student_id}&lang=en_GB'
    )
    return student.json()
