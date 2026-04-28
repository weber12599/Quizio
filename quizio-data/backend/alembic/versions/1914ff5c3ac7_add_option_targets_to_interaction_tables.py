"""add option targets to interaction tables

Revision ID: 1914ff5c3ac7
Revises: 153f8dca530a
Create Date: 2026-04-26 15:13:14.448984

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1914ff5c3ac7'
down_revision: Union[str, Sequence[str], None] = '153f8dca530a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # interaction_comments: extend with option target columns
    op.add_column('interaction_comments', sa.Column('question_id', sa.Integer(), nullable=True))
    op.add_column('interaction_comments', sa.Column('option_index', sa.Integer(), nullable=True))
    op.alter_column('interaction_comments', 'answer_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.create_foreign_key(
        'interaction_comments_question_id_fkey',
        'interaction_comments', 'questions',
        ['question_id'], ['id'], ondelete='RESTRICT',
    )
    op.create_check_constraint(
        'interaction_comments_single_target_check',
        'interaction_comments',
        '(CASE WHEN answer_id IS NOT NULL THEN 1 ELSE 0 END + '
        'CASE WHEN (question_id IS NOT NULL AND option_index IS NOT NULL) '
        'THEN 1 ELSE 0 END) = 1',
    )

    # interaction_likes: extend target options with question option
    op.add_column('interaction_likes', sa.Column('question_id', sa.Integer(), nullable=True))
    op.add_column('interaction_likes', sa.Column('option_index', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'interaction_likes_question_id_fkey',
        'interaction_likes', 'questions',
        ['question_id'], ['id'], ondelete='RESTRICT',
    )
    op.drop_constraint(
        'interaction_likes_single_target_check',
        'interaction_likes',
        type_='check',
    )
    op.create_check_constraint(
        'interaction_likes_single_target_check',
        'interaction_likes',
        '(CASE WHEN answer_id IS NOT NULL THEN 1 ELSE 0 END + '
        'CASE WHEN comment_id IS NOT NULL THEN 1 ELSE 0 END + '
        'CASE WHEN (question_id IS NOT NULL AND option_index IS NOT NULL) '
        'THEN 1 ELSE 0 END) = 1',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'interaction_likes_single_target_check',
        'interaction_likes',
        type_='check',
    )
    op.create_check_constraint(
        'interaction_likes_single_target_check',
        'interaction_likes',
        '(CASE WHEN answer_id IS NOT NULL THEN 1 ELSE 0 END + '
        'CASE WHEN comment_id IS NOT NULL THEN 1 ELSE 0 END) = 1',
    )
    op.drop_constraint('interaction_likes_question_id_fkey', 'interaction_likes', type_='foreignkey')
    op.drop_column('interaction_likes', 'option_index')
    op.drop_column('interaction_likes', 'question_id')

    op.drop_constraint(
        'interaction_comments_single_target_check',
        'interaction_comments',
        type_='check',
    )
    op.drop_constraint('interaction_comments_question_id_fkey', 'interaction_comments', type_='foreignkey')
    op.alter_column('interaction_comments', 'answer_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_column('interaction_comments', 'option_index')
    op.drop_column('interaction_comments', 'question_id')
