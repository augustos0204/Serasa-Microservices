"""add_is_processed_to_file_metadata

Revision ID: 3dd5cc68fd44
Revises: 27ed065ae2cc
Create Date: 2025-09-14 13:18:17.108169

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '3dd5cc68fd44'
down_revision: Union[str, Sequence[str], None] = '27ed065ae2cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('file_metadata', sa.Column('is_processed', sa.Boolean(), nullable=True, comment='Indica se o arquivo já foi processado'))

    op.execute("UPDATE file_metadata SET is_processed = FALSE WHERE is_processed IS NULL")

    op.alter_column('file_metadata', 'is_processed', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('file_metadata', 'is_processed')
