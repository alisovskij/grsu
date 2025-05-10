from sqlalchemy import String
from src.utils.database.db import Base
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(255),unique=True)
    email: Mapped[str] = mapped_column(String(255),unique=True)
    password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(255), default='teacher')
    post: Mapped[str] = mapped_column(String(255))
    schedule_id: Mapped[str] = mapped_column(String(36))
