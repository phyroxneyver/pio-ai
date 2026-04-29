"""Create feedback_ia table

Revision ID: 8810d8886b18
Revises: 2700da73ddfb
Create Date: 2026-04-28 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8810d8886b18'
down_revision: Union[str, Sequence[str], None] = '2700da73ddfb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create feedback_ia table."""
    op.create_table(
        'feedback_ia',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('imagen_id', sa.Integer(), nullable=False),
        sa.Column('resultado_ia_id', sa.Integer(), nullable=True),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('conteo_ia', sa.Integer(), nullable=True),
        sa.Column('conteo_corregido', sa.Integer(), nullable=False),
        sa.Column('diferencia', sa.Integer(), nullable=False),
        sa.Column('tipo_feedback', sa.String(30), nullable=False, server_default='correccion'),
        sa.Column('motivo', sa.Text(), nullable=True),
        sa.Column('imagen_url', sa.String(500), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['imagen_id'], ['imagenes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resultado_ia_id'], ['resultados_ia.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['usuario_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_feedback_ia_imagen_id', 'imagen_id'),
        sa.Index('ix_feedback_ia_usuario_id', 'usuario_id'),
    )


def downgrade() -> None:
    """Downgrade schema - Drop feedback_ia table."""
    op.drop_table('feedback_ia')
