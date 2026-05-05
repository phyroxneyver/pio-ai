"""add coordenadas to resultados_ia

Revision ID: 348a041b3611
Revises: 8810d8886b18
Create Date: 2026-05-05 17:56:27.620298

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '348a041b3611'
down_revision: Union[str, Sequence[str], None] = '8810d8886b18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add coordenadas to resultados_ia."""
    op.add_column('resultados_ia', sa.Column('coordenadas', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema - Remove coordenadas from resultados_ia."""
    op.drop_column('resultados_ia', 'coordenadas')
