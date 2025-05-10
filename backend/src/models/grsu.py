from sqlalchemy import Integer, String, ForeignKey, Time, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.user import User
from src.utils.database.db import Base


class Faculty(Base):
    __tablename__ = 'faculties'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True)
    groups: Mapped[list["Group"]] = relationship("Group", back_populates="faculty")


class Department(Base):
    __tablename__ = 'departments'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True)


class Student(Base):
    __tablename__ = 'students'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    order: Mapped[int] = mapped_column(Integer)

    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("groups.id"))
    group: Mapped["Group"] = relationship("Group", back_populates="students")


class Group(Base):
    __tablename__ = 'groups'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True)
    students_value: Mapped[int] = mapped_column(Integer)

    faculty_id: Mapped[int] = mapped_column(Integer, ForeignKey('faculties.id'))
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey('departments.id'))

    faculty: Mapped["Faculty"] = relationship("Faculty", back_populates="groups")
    department: Mapped["Department"] = relationship("Department")

    lessons: Mapped[list["Lesson"]] = relationship("Lesson", secondary="lesson_groups", back_populates="groups")
    students: Mapped[list["Student"]] = relationship("Student", back_populates="group")


class Lesson(Base):
    __tablename__ = 'lessons'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True)
    type: Mapped[str] = mapped_column(String)
    label: Mapped[str] = mapped_column(String, nullable=True)
    time_start: Mapped[Time] = mapped_column(Time)
    time_end: Mapped[Time] = mapped_column(Time)
    date: Mapped[Date] = mapped_column(Date)
    address: Mapped[str] = mapped_column(String)
    room: Mapped[str] = mapped_column(String)
    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))

    groups: Mapped[list["Group"]] = relationship("Group", secondary="lesson_groups", back_populates="lessons")
    teacher: Mapped["User"] = relationship("User")


class Attendance(Base):
    __tablename__ = 'attendance'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey('students.id'))
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey('lessons.id'))
    detected: Mapped[bool] = mapped_column(Boolean, default=False)

    student: Mapped["Student"] = relationship("Student")
    lesson: Mapped["Lesson"] = relationship("Lesson")


class LessonGroup(Base):
    __tablename__ = 'lesson_groups'

    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey('lessons.id'), primary_key=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey('groups.id'), primary_key=True)


class Report(Base):
    __tablename__ = 'reports'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey('lessons.id'))
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey('groups.id'))
    image_path: Mapped[str] = mapped_column(String)

    lesson: Mapped["Lesson"] = relationship("Lesson")
    group: Mapped["Group"] = relationship("Group")
