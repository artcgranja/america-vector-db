"""update_document_models

Revision ID: 9280bdb6090d
Revises: 528bbc349558
Create Date: 2025-05-31 13:05:36.244222

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9280bdb6090d'
down_revision: Union[str, None] = '528bbc349558'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
