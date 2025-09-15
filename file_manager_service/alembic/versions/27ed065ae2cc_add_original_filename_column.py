"""Add original_filename column

Revision ID: 27ed065ae2cc
Revises: c4fe68bde894
Create Date: 2025-09-14 02:27:55.297811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '27ed065ae2cc'
down_revision: Union[str, Sequence[str], None] = 'c4fe68bde894'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('file_metadata', sa.Column('original_filename', sa.String(length=255), nullable=True, comment='Nome original do arquivo'))

    op.execute("""
        UPDATE file_metadata
        SET original_filename = substring(file_path from '([^/]+)$')
        WHERE original_filename IS NULL
    """)

    op.alter_column('file_metadata', 'original_filename', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('file_metadata', 'original_filename')
