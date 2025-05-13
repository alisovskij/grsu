from typing import List, Dict

from sqlalchemy import select

from src.models.grsu import Student, Attendance
from src.utils.database.session import SessionDep


async def get_students_by_group(
        group_id: int,
        db: SessionDep
) -> List[Student]:

    students = (
        await db.execute(
            select(Student).where(
                Student.group_id == group_id
            ).order_by(Student.order)
        )
    ).scalars().all()

    return students


async def get_attendance_map(
        lesson_id: int,
        student_ids: List[int],
        db: SessionDep
) -> Dict[int, bool]:

    if not student_ids:
        return {}

    attendance_records = (
        await db.execute(
            select(Attendance).where(
                Attendance.lesson_id == lesson_id,
                Attendance.student_id.in_(student_ids)
            )
        )
    ).scalars().all()

    return {record.student_id: record.detected for record in attendance_records}