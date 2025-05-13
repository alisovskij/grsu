from fastapi import HTTPException
from sqlalchemy import select

from src.models.grsu import Report, Lesson
from src.utils.database.session import SessionDep


async def get_report_by_id(
        report_id: int,
        db: SessionDep
) -> Report:

    report = (
        await db.execute(
            select(Report).where(
                Report.id == report_id
            )
        )
    ).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Отчет не найден")
    return report



async def verify_lesson_access(
        lesson_id: int,
        teacher_id: int,
        db: SessionDep
) -> Lesson:

    lesson = (
        await db.execute(
            select(Lesson)
            .where(
                Lesson.id == lesson_id,
                Lesson.teacher_id == teacher_id,
            )
        )
    ).scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=403, detail="У вас нет доступа к этому отчету")

    return lesson


async def get_report_for_teacher(
        lesson_id: int,
        group_id: int,
        db: SessionDep
) -> Report:

    report = (
        await db.execute(
            select(Report).where(
                Report.lesson_id == lesson_id,
                Report.group_id == group_id,
            )
        )
    ).scalar_one_or_none()

    return report