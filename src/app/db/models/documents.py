from sqlalchemy import Column, String, DateTime, func, Integer, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship
from src.app.db.base import Base

class DocumentBaseModel(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    document_type = Column(String, nullable=False)
    document_number = Column(Integer, nullable=True)
    document_year = Column(Integer, nullable=True)
    document_name = Column(String, nullable=False)
    presented_by = Column(String, nullable=True)
    presented_at = Column(DateTime(timezone=True), nullable=True)
    summary = Column(String, nullable=True)
    central_theme = Column(String, nullable=True)
    key_points = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, filename={self.filename})>"

class PrimaryDocumentModel(DocumentBaseModel):
    __tablename__ = "primary_documents"
    __table_args__ = {'extend_existing': True}
    
    collection_name = Column(String, nullable=False)
    
    secondary_documents = relationship("SecondaryDocumentModel", back_populates="primary")
    
    # Relacionamento com os subjects
    subjects = relationship("SubjectModel", secondary="primary_subjects", back_populates="primary_documents")

class SecondaryDocumentModel(DocumentBaseModel):
    __tablename__ = "secondary_documents"
    __table_args__ = {'extend_existing': True}

    role = Column(String, nullable=True)
    party_affiliation = Column(String, nullable=False)
    
    primary_id = Column(Integer, ForeignKey("primary_documents.id"), nullable=False)
    primary = relationship("PrimaryDocumentModel", back_populates="secondary_documents")

    # Relacionamento com os subjects
    subjects = relationship("SubjectModel", secondary="secondary_subjects", back_populates="secondary_documents")