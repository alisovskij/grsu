from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.future import select
import requests

from src.models.grsu import Lesson, Faculty, Department, Group, LessonGroup
from src.models.user import User
from src.utils.database.session import SessionDep


async def find_lesson_in_grsu(
        lesson_id: int,
        user: User,
        group_id: int,
        date: str,
        db: SessionDep
) -> Lesson:
    try:
        lesson_date = datetime.strptime(date, "%d.%m.%Y").date().strftime("%d.%m.%Y")
    except ValueError:
        raise HTTPException(status_code=404, detail="Неверный формат даты. Используйте ДД.MM.ГГГГ.")

    response = requests.get(
        f'http://api.grsu.by/1.x/app2/getTeacherSchedule?teacherId={user.schedule_id}&dateStart={lesson_date}&dateEnd={lesson_date}'
    )

    if response.json()['count'] == 0:
        raise HTTPException(status_code=200, detail="В этот день нету занятий")

    lessons = response.json()['days'][0]['lessons']
    lesson_data = next((lesson for lesson in lessons if lesson['id'] == str(lesson_id)), None)

    if not lesson_data:
        raise HTTPException(status_code=404, detail=f"Урок с ID {lesson_id} не найден")

    group_data_list = lesson_data['groups']

    faculty_data = group_data_list[0]['faculty']
    department_data = group_data_list[0]['department']

    faculty = await db.execute(select(Faculty).filter(Faculty.id == int(faculty_data['id'])))
    faculty = faculty.scalars().first()
    if not faculty:
        faculty = Faculty(id=int(faculty_data['id']), title=faculty_data['title'])
        db.add(faculty)

    department = await db.execute(select(Department).filter(Department.id == int(department_data['id'])))
    department = department.scalars().first()
    if not department:
        department = Department(id=int(department_data['id']), title=department_data['title'])
        db.add(department)

    lesson = await db.execute(select(Lesson).filter(Lesson.id == int(lesson_data['id'])))
    lesson = lesson.scalars().first()
    if not lesson:
        lesson = Lesson(
            id=int(lesson_data['id']),
            title=lesson_data['title'],
            type=lesson_data['type'],
            label=lesson_data.get('label', ""),
            time_start=datetime.strptime(lesson_data['timeStart'], "%H:%M").time(),
            time_end=datetime.strptime(lesson_data['timeEnd'], "%H:%M").time(),
            address=lesson_data['address'],
            room=lesson_data['room'],
            date=datetime.strptime(response.json()['days'][0]['date'], "%Y-%m-%d").date(),
            teacher_id = user.id
        )
        db.add(lesson)

    for group_data in group_data_list:
        group = await db.execute(select(Group).filter(Group.id == int(group_data['id'])))
        group = group.scalars().first()
        if not group:
            group = Group(
                id=int(group_data['id']),
                title=group_data['title'],
                students_value=int(group_data['students']),
                faculty_id=int(faculty_data['id']),
                department_id=int(department_data['id']),
            )
            db.add(group)


    try:
        lesson_group = LessonGroup(lesson_id=int(lesson.id), group_id=int(group_id))
        db.add(lesson_group)

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail="Такой отчет уже есть")


    return lesson
