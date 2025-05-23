"""add table students

Revision ID: 908e8e4f51ee
Revises: 7b2b3e74e076
Create Date: 2025-05-07 23:56:42.540833

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '908e8e4f51ee'
down_revision: Union[str, None] = '7b2b3e74e076'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('students',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_column('groups', 'students')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('groups', sa.Column('students', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_table('students')
    # ### end Alembic commands ###
