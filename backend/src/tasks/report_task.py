import os
import cv2
from deepface import DeepFace
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.models.grsu import Student, Attendance
from src.tasks.celery_app import celery

@celery.task(bind=True)
def process_attendance(self, lesson_id: int, group_id: int):
    import asyncio
    asyncio.run(_process_attendance(lesson_id, group_id, self.request.id))

async def _process_attendance(
    lesson_id: int,
    group_id: int,
    request_id: str
):
    redis = Redis(host="redis", port=6379, db=0)
    engine = create_async_engine("postgresql+asyncpg://grsu:1111@db/grsudb")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as db:
        group_img_path = os.path.join(
            os.getcwd(),
            "images",
            "reports",
            f"report_{lesson_id}_{group_id}.jpg"
        )

        if not os.path.exists(group_img_path):
            raise FileNotFoundError(f"Групповое фото не найдено: {group_img_path}")

        detected_faces = DeepFace.extract_faces(
            img_path=group_img_path,
            enforce_detection=False,
            align=True
        )

        students_result = await db.execute(
            select(Student).where(Student.group_id == group_id)
        )
        students = students_result.scalars().all()

        total = len(students)
        for index, student in enumerate(students):
            ref_img_path = os.path.join(
                os.getcwd(),
                "images",
                "students",
                f"{student.id}.jpg"
            )

            if not os.path.exists(ref_img_path):
                continue

            is_present = False

            for idx, face in enumerate(detected_faces):
                cropped_face = face["face"]

                if cropped_face.max() <= 1.0:
                    cropped_face = (cropped_face * 255).astype("uint8")

                temp_face_path = os.path.join(
                    os.getcwd(),
                    "images",
                    "reports",
                    f"temp_face_{student.id}_{idx}.jpg"
                )
                cv2.imwrite(temp_face_path, cropped_face)

                result = DeepFace.verify(
                    img1_path=ref_img_path,
                    img2_path=temp_face_path,
                    model_name="ArcFace",
                    enforce_detection=False
                )

                os.remove(temp_face_path)

                if result["verified"]:
                    is_present = True
                    break

            attendance = Attendance(
                student_id=student.id,
                lesson_id=lesson_id,
                detected=is_present
            )
            db.add(attendance)

            percent = int((index + 1) / total * 100)
            await redis.set(f"task_progress:{request_id}", percent)

        await db.commit()

        await redis.set(f"task_progress:{request_id}", 100)
