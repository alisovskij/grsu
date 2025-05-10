"""add date column to lessons

Revision ID: db2dee334ca8
Revises: ac28c029a71e
Create Date: 2025-05-06 22:49:49.569675

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db2dee334ca8'
down_revision: Union[str, None] = 'ac28c029a71e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('lessons', sa.Column('date', sa.Date(), nullable=True))
    pass


def downgrade() -> None:
    op.drop_column('lessons', 'date')
    pass
