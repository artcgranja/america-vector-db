from sqlalchemy import Column, String, DateTime, func, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship
from src.app.db.base import Base

# Association table for many-to-many relationship between MPVs and subjects
mpv_subjects = Table(
    'mpv_subjects',
    Base.metadata,
    Column('mpv_id', Integer, ForeignKey('mpvs.id'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('subjects.id'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now(), nullable=False)
)

# Association table for many-to-many relationship between Emendas and subjects
emenda_subjects = Table(
    'emenda_subjects',
    Base.metadata,
    Column('emenda_id', Integer, ForeignKey('document_emendas.id'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('subjects.id'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now(), nullable=False)
)

class SubjectModel(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships with documents
    mpvs = relationship("MPVModel", secondary=mpv_subjects, back_populates="subjects")
    emendas = relationship("DocumentEmendaModel", secondary=emenda_subjects, back_populates="subjects")