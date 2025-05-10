from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from src.core.config import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]