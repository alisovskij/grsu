# Версия с анализом
# import os
# import cv2
# from deepface import DeepFace
# from sqlalchemy.ext.asyncio import AsyncSession
# from src.models.grsu import Student, Attendance
# from sqlalchemy import select
#
#
# async def process_attendance(lesson_id: int, group_id: int, db: AsyncSession):
#
#     group_img_path = os.path.join(os.getcwd(), "images", "reports", f"report_{lesson_id}_{group_id}.jpg")
#     if not os.path.exists(group_img_path):
#         raise FileNotFoundError(f"Групповое фото не найдено: {group_img_path}")
#
#     print(f"📸 Загружено групповое фото: {group_img_path}")
#
#
#     result = await db.execute(select(Student).where(Student.group_id == group_id))
#     students = result.scalars().all()
#
#     if not students:
#         print("❌ Нет студентов в группе")
#         return
#
#
#     detected_faces = DeepFace.extract_faces(img_path=group_img_path, enforce_detection=False, align=True)
#
#     print(f"👥 Найдено лиц на фото: {len(detected_faces)}")
#
#     for student in students:
#         reference_img_path = os.path.join(os.getcwd(), "images", "students", f"{student.id}.jpg")
#
#         if not os.path.exists(reference_img_path):
#             print(f"⚠️ Эталонное фото отсутствует для студента {student.name} (ID: {student.id})")
#             continue
#
#         is_present = False
#
#         for idx, face in enumerate(detected_faces):
#             cropped_face = face["face"]
#
#             if cropped_face.max() <= 1.0:
#                 cropped_face = (cropped_face * 255).astype("uint8")
#
#             temp_face_path = os.path.join(os.getcwd(), "images", "reports", f"temp_face_{student.id}_{idx}.jpg")
#             cv2.imwrite(temp_face_path, cropped_face)
#
#
#             result = DeepFace.verify(
#                 img1_path=reference_img_path,
#                 img2_path=temp_face_path,
#                 model_name="ArcFace",
#                 enforce_detection=False
#             )
#
#             print(
#                 f"👉 Проверка студента {student.name} с лицом #{idx + 1}: verified={result['verified']}, distance={result['distance']}")
#
#             if result["verified"]:
#                 is_present = True
#                 print(f"✅ {student.name} найден на фото (лицо #{idx + 1})")
#
#
#                 analysis_dir = os.path.join(os.getcwd(), "images", "analysis", f"{lesson_id}_{group_id}",
#                                             str(student.id))
#                 os.makedirs(analysis_dir, exist_ok=True)
#
#                 saved_ref = os.path.join(analysis_dir, "reference.jpg")
#                 saved_found = os.path.join(analysis_dir, f"found_face_{idx + 1}.jpg")
#
#                 cv2.imwrite(saved_ref, cv2.imread(reference_img_path))
#                 cv2.imwrite(saved_found, cropped_face)
#
#                 break
#             else:
#
#                 pass
#
#             os.remove(temp_face_path)
#
#
#         attendance = Attendance(
#             student_id=student.id,
#             lesson_id=lesson_id,
#             detected=is_present
#         )
#         db.add(attendance)
#
#     await db.commit()
#     print(f"📝 Отчет сформирован и записан для урока {lesson_id}, группы {group_id}")

import os
import cv2
from deepface import DeepFace
from sqlalchemy import select

from src.utils.database.session import SessionDep
from src.models.grsu import Student, Attendance

async def process_attendance(lesson_id: int, group_id: int, db: SessionDep):
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

    # print(f"🖼️ Найдено {len(detected_faces)} лиц на групповом фото")

    students = await db.execute(
        select(Student).where(Student.group_id == group_id)
    )
    students = students.scalars().all()

    for student in students:
        ref_img_path = os.path.join(
            os.getcwd(),
            "images",
            "students",
            f"{student.id}.jpg"
        )

        if not os.path.exists(ref_img_path):
            # print(f"⚠️ Эталонное фото не найдено: {ref_img_path}")
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
                # print(f"✅ {student.name} найден на фото (лицо #{idx + 1})")
                break

        attendance = Attendance(
            student_id=student.id,
            lesson_id=lesson_id,
            detected=is_present
        )
        db.add(attendance)

    await db.commit()
    # print("🎉 Посещаемость сохранена")
