"""add session_id to student_submissions

Revision ID: c5687426d36b
Revises: 4b1143bee86e
Create Date: 2026-04-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5687426d36b'
down_revision: Union[str, Sequence[str], None] = '4b1143bee86e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('student_submissions',
        sa.Column('session_id', sa.String(36), nullable=True)
    )
    op.create_index(op.f('ix_student_submissions_session_id'), 'student_submissions', ['session_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_student_submissions_session_id'), table_name='student_submissions')
    op.drop_column('student_submissions', 'session_id')
