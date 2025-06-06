"""descrição da alteração

Revision ID: c577a019ae53
Revises: 9280bdb6090d
Create Date: 2025-05-31 13:21:12.662589

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c577a019ae53'
down_revision: Union[str, None] = '9280bdb6090d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('document_emendas', 'document_metadata')
    op.drop_column('mpvs', 'ementa')
    op.drop_column('mpvs', 'document_metadata')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('mpvs', sa.Column('document_metadata', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('mpvs', sa.Column('ementa', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.add_column('document_emendas', sa.Column('document_metadata', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
