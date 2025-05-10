from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.future import select
from src.models.grsu import Lesson, Faculty, Department, Group, LessonGroup
import requests

from src.models.user import User
from src.utils.database.session import SessionDep


async def find_lesson_in_grsu(lesson_id: int, teacher_id: str, group_id: int, db: SessionDep):
    # в конечной версии строку раскомментировать
    # date = datetime.now().strftime('%d.%m.%Y')

    date = '29.01.2025' # постить отчет к паре можно только в случае, если пара в этот день, для теста можно менять дату
    teacher = (
        await db.execute(
            select(User).where(User.id == teacher_id)
        )
    ).scalar_one_or_none()

    if not teacher:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")

    response = requests.get(
        f'http://api.grsu.by/1.x/app2/getTeacherSchedule?teacherId={teacher.schedule_id}&dateStart={date}&dateEnd={date}&lang=en_GB'
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
        await db.commit()

    department = await db.execute(select(Department).filter(Department.id == int(department_data['id'])))
    department = department.scalars().first()
    if not department:
        department = Department(id=int(department_data['id']), title=department_data['title'])
        db.add(department)
        await db.commit()

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
            teacher_id = teacher.id
        )
        db.add(lesson)
        await db.commit()

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
            await db.commit()


    lesson_group = LessonGroup(lesson_id=int(lesson.id), group_id=int(group_id))
    db.add(lesson_group)

    await db.commit()

    return lesson
