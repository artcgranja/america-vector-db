"""add_central_theme_and_key_points_to_documents

Revision ID: 9d2f2860edd5
Revises: 0f22597efc7c
Create Date: 2025-06-16 22:19:06.996832

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '9d2f2860edd5'
down_revision: Union[str, None] = '0f22597efc7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add columns to primary_documents
    op.add_column('primary_documents', sa.Column('central_theme', sa.String(), nullable=True))
    op.add_column('primary_documents', sa.Column('key_points', JSONB, nullable=True))
    
    # Add columns to secondary_documents
    op.add_column('secondary_documents', sa.Column('central_theme', sa.String(), nullable=True))
    op.add_column('secondary_documents', sa.Column('key_points', JSONB, nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove columns from secondary_documents
    pass
