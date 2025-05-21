import asyncio
import os
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Depends
from sqlalchemy import select, desc
from starlette.websockets import WebSocket

from src.dependencies.user import get_current_user
from src.models.grsu import Lesson, Group, Report
from src.models.user import User
from src.services.find_lesson import find_lesson_in_grsu
from src.tasks.report_task import process_attendance
from src.services.report_service import get_report_by_id, verify_lesson_access, get_report_for_teacher
from src.services.student_service import get_students_by_group, get_attendance_map
from src.utils.database.session import SessionDep
from src.utils.file import save_upload_file
from src.core.config import redis

router = APIRouter()

UPLOAD_DIR = "images"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post('/create')
async def create_report(
    lesson_id: int,
    group_id: int,
    date: str,
    db: SessionDep,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    try:
        lesson = await find_lesson_in_grsu(lesson_id, user, group_id, date, db)

        filename = f"report_{lesson.id}_{group_id}.jpg"
        file_path = await save_upload_file(file, "images/reports", filename)

        report = Report(
            lesson_id=lesson.id,
            group_id=group_id,
            image_path=file_path
        )

        db.add(report)
        await db.commit()
        await db.refresh(report)

        attendance = process_attendance.delay(lesson_id, group_id)

        return {"task": attendance.id, "report": report.id}


    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except IntegrityError as e:
        if "duplicate key" in str(e.orig):
            raise HTTPException(status_code=404, detail="Такой отчет уже есть")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка на сервере, {str(e)}")

    finally:
        if db.is_active:
            await db.rollback()

@router.get("")
async def get_reports_for_teacher(
    db: SessionDep,
    dateStart: str = Query(..., description="Дата начала в формате ДД.MM.ГГГГ"),
    dateEnd: str = Query(..., description="Дата конца в формате ДД.MM.ГГГГ"),
    user: User = Depends(get_current_user)
):
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
            Lesson.teacher_id == user.id,
            Lesson.date >= start_date,
            Lesson.date <= end_date
        ).order_by(desc(Lesson.date))
    )

    result = await db.execute(lessons_query)
    lessons = result.scalars().unique().all()

    lessons_data = []

    for lesson in lessons:
        groups_data = []
        for group in lesson.groups:
            report = await get_report_for_teacher(lesson.id, group.id, db)

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
async def get_report(
        report_id: int,
        db: SessionDep,
        user: User = Depends(get_current_user)
):

    report = await get_report_by_id(report_id, db)
    lesson = await verify_lesson_access(report.lesson_id, user.id, db)
    students = await get_students_by_group(report.group_id, db)

    attendance_map = await get_attendance_map(lesson.id, [s.id for s in students], db)

    return {
        "report_id": report.id,
        "image_url": report.image_path,
        "students": [
            {
                "id": student.id,
                "name": student.name,
                "detected": attendance_map.get(student.id, False)
            }
            for student in students
        ]
    }


@router.websocket("/ws/progress/{task_id}")
async def websocket_progress(websocket: WebSocket, task_id: str):
    await websocket.accept()

    try:
        while True:
            progress = await redis.get(f"task_progress:{task_id}")

            if progress is None:
                await asyncio.sleep(0.5)
                continue

            await websocket.send_json({"progress": int(progress)})

            if int(progress) >= 100:
                await redis.set(f"task_progress:{task_id}", "success")
                break

            await asyncio.sleep(0.5)

    finally:
        await websocket.close()
