import asyncio
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.models.grsu import Student, Group, Faculty, Department
from src.utils.database.session import get_session

async def import_students_from_excel(file_path: str):
    gen = get_session()
    db = await gen.__anext__()

    try:
        df = pd.read_excel(file_path)
        df = df[df["ID"].notna()]

        for _, row in df.iterrows():
            group_id = int(row["GROUP ID"])

            # --- проверяем faculty
            faculty_id = 3  # замените на значение по умолчанию или возьмите из данных
            faculty = await db.get(Faculty, faculty_id)
            if not faculty:
                faculty = Faculty(
                    id=faculty_id,
                    title="ФаМИ"
                )
                db.add(faculty)
                await db.flush()

            # --- проверяем department
            department_id = 2  # замените на значение по умолчанию или возьмите из данных
            department = await db.get(Department, department_id)
            if not department:
                department = Department(
                    id=department_id,
                    title="д/о"
                )
                db.add(department)
                await db.flush()

            # --- проверяем группу
            group = await db.get(Group, group_id)
            if not group:
                group = Group(
                    id=group_id,
                    title="СДП-КБ-211", # СДП-УИР-211
                    students_value=22, # не менять
                    faculty_id=faculty.id,
                    department_id=department.id
                )
                db.add(group)
                await db.flush()

            # --- добавляем студента
            student = Student(
                id=int(row["ID"]),
                order=int(row["ORDER"]) if not pd.isna(row["ORDER"]) else None,
                name=str(row["NAME"]),
                email=str(row["MAIL"]),
                group_id=group_id
            )
            db.add(student)

        await db.commit()
    finally:
        await db.close()
        await gen.aclose()

    print("✅ Студенты, группы, факультеты и кафедры успешно добавлены.")

if __name__ == "__main__":
    asyncio.run(import_students_from_excel("13118.xlsx"))
