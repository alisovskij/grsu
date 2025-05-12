import os
import shutil
from datetime import datetime
from sqlalchemy.orm import selectinload
from fastapi import APIRouter, Request, File, UploadFile, HTTPException, Query
from sqlalchemy import select

from src.api.routes.auth import SESSION_KEY
from src.models.grsu import Lesson, Group, Report, Student, Attendance
from src.models.user import User
from src.services.find_lesson import find_lesson_in_grsu
from src.services.find_student import process_attendance
from src.utils.database.session import SessionDep

router = APIRouter()

UPLOAD_DIR = "images"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post('/create')
async def create_report(
    lesson_id: int,
    group_id: int,
    date: str,
    db: SessionDep,
    request: Request,
    file: UploadFile = File(...)
):
    try:
        user_id = request.session.get(SESSION_KEY)
        if not user_id:
            raise HTTPException(status_code=401, detail="Требуется авторизация")

        lesson = await find_lesson_in_grsu(lesson_id, user_id, group_id, date, db)

        save_dir = os.path.join("images", "reports")
        os.makedirs(save_dir, exist_ok=True)

        filename = f"report_{lesson.id}_{group_id}.jpg"
        file_path = os.path.join(save_dir, filename)

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        await process_attendance(lesson.id, group_id, db)

        report = Report(
            lesson_id=lesson.id,
            group_id=group_id,
            image_path=file_path
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)
        return {"report_id": report.id, "image_path": report.image_path}

    except HTTPException as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e.detail))

    except FileNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка на сервере, {str(e)}")

@router.get("")
async def get_lessons_for_teacher(
    request: Request,
    db: SessionDep,
    dateStart: str = Query(..., description="Дата начала в формате ДД.MM.ГГГГ"),
    dateEnd: str = Query(..., description="Дата конца в формате ДД.MM.ГГГГ")
):
    user_id = request.session.get(SESSION_KEY)
    if not user_id:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    teacher = (
        await db.execute(
            select(User).where(User.id == user_id)
        )
    ).scalar_one_or_none()

    if not teacher:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")

    try:
        start_date = datetime.strptime(dateStart, "%d.%m.%Y").date()
        end_date = datetime.strptime(dateEnd, "%d.%m.%Y").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты. Используйте ДД.MM.ГГГГ.")

    lessons_query = (
        select(Lesson)
        .options(
            selectinload(Lesson.groups).selectinload(Group.faculty),
            selectinload(Lesson.groups).selectinload(Group.department),
            selectinload(Lesson.teacher)
        )
        .where(
            Lesson.teacher_id == user_id,
            Lesson.date >= start_date,
            Lesson.date <= end_date
        )
    )

    result = await db.execute(lessons_query)
    lessons = result.scalars().unique().all()

    lessons_data = []

    for lesson in lessons:
        groups_data = []
        for group in lesson.groups:
            report = (
                await db.execute(
                    select(Report)
                    .where(Report.lesson_id == lesson.id, Report.group_id == group.id)
                )
            ).scalar_one_or_none()

            groups_data.append({
                "id": group.id,
                "title": group.title,
                "students": group.students_value,
                "faculty": {
                    "id": group.faculty.id,
                    "title": group.faculty.title
                } if group.faculty else None,
                "department": {
                    "id": group.department.id,
                    "title": group.department.title
                } if group.department else None,
                "report": {
                    "id": report.id if report else None,
                    "image_url": f'/{report.image_path}'
                }
            })

        lesson_info = {
            "id": lesson.id,
            "title": lesson.title,
            "type": lesson.type,
            "date": lesson.date.strftime("%d.%m.%Y"),
            "time_start": lesson.time_start.strftime("%H:%M"),
            "time_end": lesson.time_end.strftime("%H:%M"),
            "address": lesson.address,
            "room": lesson.room,
            "groups": groups_data
        }
        lessons_data.append(lesson_info)

    return {"count": len(lessons_data), "lessons": lessons_data}


@router.get("/{report_id}")
async def get_report(report_id: int, request: Request, db: SessionDep):
    user_id = request.session.get(SESSION_KEY)
    if not user_id:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    report = (
        await db.execute(
            select(Report)
            .where(Report.id == report_id)
        )
    ).scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Отчет не найден")

    lesson = (
        await db.execute(
            select(Lesson)
            .where(
                Lesson.id == report.lesson_id,
                Lesson.teacher_id == user_id
            )
        )
    ).scalar_one_or_none()

    if not lesson:
        raise HTTPException(status_code=403, detail="У вас нет доступа к этому отчету")

    students = (
        await db.execute(
            select(Student)
            .where(Student.group_id == report.group_id).order_by(Student.order)
        )
    ).scalars().all()

    attendance_records = (
        await db.execute(
            select(Attendance)
            .where(
                Attendance.lesson_id == report.lesson_id,
                Attendance.student_id.in_([s.id for s in students])
            )
        )
    ).scalars().all()

    attendance_map = {record.student_id: record.detected for record in attendance_records}

    students_data = []
    for student in students:
        students_data.append({
            "id": student.id,
            "name": student.name,
            "detected": attendance_map.get(student.id, False)
        })


    return {
        "report_id": report.id,
        "image_url": report.image_path,
        "students": students_data
    }


