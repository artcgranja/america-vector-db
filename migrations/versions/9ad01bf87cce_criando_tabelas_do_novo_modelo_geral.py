"""criando tabelas do novo modelo geral

Revision ID: 9ad01bf87cce
Revises: 1503edb2e8ca
Create Date: 2025-06-16 21:47:04.339848

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ad01bf87cce'
down_revision: Union[str, None] = '1503edb2e8ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Criando tabela de subjects
    op.create_table(
        'subjects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Criando tabela de primary_documents
    op.create_table(
        'primary_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('document_type', sa.String(), nullable=False),
        sa.Column('document_name', sa.String(), nullable=False),
        sa.Column('presented_by', sa.String(), nullable=True),
        sa.Column('presented_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('summary', sa.String(), nullable=True),
        sa.Column('collection_name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Criando tabela de secondary_documents
    op.create_table(
        'secondary_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('document_type', sa.String(), nullable=False),
        sa.Column('document_name', sa.String(), nullable=False),
        sa.Column('presented_by', sa.String(), nullable=True),
        sa.Column('presented_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('summary', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('party_affiliation', sa.String(), nullable=False),
        sa.Column('primary_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['primary_id'], ['primary_documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Criando tabela de associação primary_subjects
    op.create_table(
        'primary_subjects',
        sa.Column('primary_document_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['primary_document_id'], ['primary_documents.id'], ),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ),
        sa.PrimaryKeyConstraint('primary_document_id', 'subject_id')
    )

    # Criando tabela de associação secondary_subjects
    op.create_table(
        'secondary_subjects',
        sa.Column('secondary_document_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['secondary_document_id'], ['secondary_documents.id'], ),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ),
        sa.PrimaryKeyConstraint('secondary_document_id', 'subject_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
