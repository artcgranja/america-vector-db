from sqlalchemy import Column, String, DateTime, func, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.base import Base

# Association table for many-to-many relationship between MPVs and subjects
primary_subjects = Table(
    'primary_subjects',
    Base.metadata,
    Column('primary_id', Integer, ForeignKey('primary_documents.id'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('subjects.id'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now(), nullable=False),
    extend_existing=True
)

# Association table for many-to-many relationship between Emendas and subjects
secondary_subjects = Table(
    'secondary_subjects',
    Base.metadata,
    Column('secondary_id', Integer, ForeignKey('secondary_documents.id'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('subjects.id'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now(), nullable=False),
    extend_existing=True
)

class SubjectModel(Base):
    __tablename__ = "subjects"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships with documents
    primary_documents = relationship("PrimaryDocumentModel", secondary=primary_subjects, back_populates="subjects")
    secondary_documents = relationship("SecondaryDocumentModel", secondary=secondary_subjects, back_populates="subjects")