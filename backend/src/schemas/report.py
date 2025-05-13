from pydantic import BaseModel


class CreateReportSchema(BaseModel):
    lesson_id: int
    group_id: int


