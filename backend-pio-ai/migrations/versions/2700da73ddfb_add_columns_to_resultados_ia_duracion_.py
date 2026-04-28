"""Add columns to resultados_ia: duracion_ms, precision_estimada, notas_ia, detecciones_json

Revision ID: 2700da73ddfb
Revises: 
Create Date: 2026-04-28 17:16:56.671964

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2700da73ddfb'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add columns to resultados_ia table
    op.add_column('resultados_ia', sa.Column('duracion_ms', sa.Integer(), nullable=True))
    op.add_column('resultados_ia', sa.Column('precision_estimada', sa.Float(), nullable=True))
    op.add_column('resultados_ia', sa.Column('notas_ia', sa.Text(), nullable=True))
    op.add_column('resultados_ia', sa.Column('detecciones_json', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove columns from resultados_ia table
    op.drop_column('resultados_ia', 'detecciones_json')
    op.drop_column('resultados_ia', 'notas_ia')
    op.drop_column('resultados_ia', 'precision_estimada')
    op.drop_column('resultados_ia', 'duracion_ms')
