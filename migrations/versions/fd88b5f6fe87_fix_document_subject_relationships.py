"""fix_document_subject_relationships

Revision ID: fd88b5f6fe87
Revises: 9d2f2860edd5
Create Date: 2024-03-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fd88b5f6fe87'
down_revision: Union[str, None] = '9d2f2860edd5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop existing association tables if they exist
    op.drop_table('primary_subjects')
    op.drop_table('secondary_subjects')
    
    # Create new primary_subjects table with proper constraints
    op.create_table(
        'primary_subjects',
        sa.Column('primary_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['primary_id'], ['primary_documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('primary_id', 'subject_id')
    )
    
    # Create new secondary_subjects table with proper constraints
    op.create_table(
        'secondary_subjects',
        sa.Column('secondary_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['secondary_id'], ['secondary_documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('secondary_id', 'subject_id')
    )


def downgrade() -> None:
    # Drop the new tables
    op.drop_table('secondary_subjects')
    op.drop_table('primary_subjects')
