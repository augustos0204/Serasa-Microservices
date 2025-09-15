"""create_file_inconsistencies_table

Revision ID: ef8a7cc57574
Revises: a175a44fe92e
Create Date: 2025-09-15 02:34:46.184089

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'ef8a7cc57574'
down_revision: Union[str, Sequence[str], None] = 'a175a44fe92e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('file_inconsistencies',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('file_id', sa.Integer(), nullable=False, comment='ID do arquivo que originou este erro'),
    sa.Column('line_number', sa.Integer(), nullable=True, comment='Número da linha com erro (null para erros estruturais)'),
    sa.Column('field_name', sa.String(length=100), nullable=True, comment='Nome do campo com erro (null para erros estruturais)'),
    sa.Column('invalid_value', sa.Text(), nullable=True, comment='Valor inválido encontrado (null para erros estruturais)'),
    sa.Column('error_message', sa.Text(), nullable=False, comment='Mensagem descritiva do erro'),
    sa.Column('error_type', sa.String(length=50), nullable=False, comment='Tipo do erro: file_invalid, missing_columns, data_validation'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='Data e hora da criação do registro'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_file_inconsistencies_id'), 'file_inconsistencies', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_file_inconsistencies_id'), table_name='file_inconsistencies')
    op.drop_table('file_inconsistencies')
