from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
import requests
from src.dependencies.user import get_current_user
from src.models.user import User


router = APIRouter()

@router.get('/schedule')
async def get_teacher_schedule(
        dateStart: str,
        dateEnd: str,
        user: User = Depends(get_current_user)
):
    try:
        schedule_date_start = datetime.strptime(dateStart, "%d.%m.%Y").date().strftime("%d.%m.%Y")
        schedule_date_end = datetime.strptime(dateEnd, "%d.%m.%Y").date().strftime("%d.%m.%Y")
    except ValueError:
        raise HTTPException(status_code=404, detail="Неверный формат даты. Используйте ДД.MM.ГГГГ.")

    schedule = requests.get(
        f'http://api.grsu.by/1.x/app2/getTeacherSchedule?teacherId={user.schedule_id}&dateStart={schedule_date_start}&dateEnd={schedule_date_end}'
    )

    return schedule.json()


@router.get('/getGroups')
async def get_teacher_schedule(
        departmentId: int,
        facultyId: int,
        course: int,
        user: User = Depends(get_current_user)
):

    groups = requests.get(
        f'http://api.grsu.by/1.x/app2/getGroups?departmentId={departmentId}&facultyId={facultyId}&course={course}'
    )

    return groups.json()


@router.get('/students')
def get_student_by_id(
        student_id: int,
        user: User = Depends(get_current_user)
):
    student = requests.get(
        f'http://api.grsu.by/1.x/app2/getStudent?login={student_id}'
    )
    return student.json()
