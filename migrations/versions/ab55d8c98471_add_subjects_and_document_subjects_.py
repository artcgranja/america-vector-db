"""add subjects and document_subjects tables

Revision ID: ab55d8c98471
Revises: c577a019ae53
Create Date: 2025-06-04 14:44:39.900603

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ab55d8c98471'
down_revision: Union[str, None] = 'c577a019ae53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
