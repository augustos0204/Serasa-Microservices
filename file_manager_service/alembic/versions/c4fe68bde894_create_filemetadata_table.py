"""Create FileMetadata table

Revision ID: c4fe68bde894
Revises:
Create Date: 2025-09-14 01:47:10.851749

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c4fe68bde894'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('file_metadata',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('file_path', sa.String(length=500), nullable=False, comment='Caminho completo do arquivo'),
    sa.Column('file_size_bytes', sa.BigInteger(), nullable=False, comment='Peso do arquivo em bytes'),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_file_metadata_id'), 'file_metadata', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_file_metadata_id'), table_name='file_metadata')
    op.drop_table('file_metadata')
