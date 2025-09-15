"""create_file_processed_data_table

Revision ID: a175a44fe92e
Revises:
Create Date: 2025-09-15 01:16:41.568554

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a175a44fe92e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('file_processed_data',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=255), nullable=False, comment='Nome completo do usuário'),
    sa.Column('documento', sa.String(length=50), nullable=False, comment='CPF ou outro documento de identificação'),
    sa.Column('telefone', sa.String(length=20), nullable=False, comment='Número de telefone'),
    sa.Column('endereco', sa.String(length=500), nullable=False, comment='Endereço completo'),
    sa.Column('file_id', sa.Integer(), nullable=False, comment='ID do arquivo que originou este registro'),
    sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='Data e hora do processamento'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('documento')
    )
    op.create_index(op.f('ix_file_processed_data_id'), 'file_processed_data', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_file_processed_data_id'), table_name='file_processed_data')
    op.drop_table('file_processed_data')
