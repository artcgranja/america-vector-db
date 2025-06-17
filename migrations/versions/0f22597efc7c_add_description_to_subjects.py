"""add_description_to_subjects

Revision ID: 0f22597efc7c
Revises: 9ad01bf87cce
Create Date: 2025-06-16 22:15:31.479020

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f22597efc7c'
down_revision: Union[str, None] = '9ad01bf87cce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('subjects', sa.Column('description', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('subjects', 'description')
