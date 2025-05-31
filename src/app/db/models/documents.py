from sqlalchemy import Column, String, DateTime, JSON, func, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class DocumentBaseModel(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    collection_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, filename={self.filename})>"

class MPVModel(DocumentBaseModel):
    __tablename__ = "mpvs"

    numero = Column(Integer, nullable=False)
    ano = Column(Integer, nullable=False)
    data_publicacao = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False)  # Em vigor, Revogada, etc.
    
    # Relacionamento com as emendas
    emendas = relationship("DocumentEmendaModel", back_populates="mpv")

class DocumentEmendaModel(DocumentBaseModel):
    __tablename__ = "document_emendas"

    num_emenda = Column(Integer, nullable=False)
    apresentada_por = Column(String, nullable=False)
    data_apresentacao = Column(DateTime(timezone=True), nullable=False)
    chunks_count = Column(Integer, default=0)
    vector_store_name = Column(String, nullable=True)
    
    mpv_id = Column(Integer, ForeignKey("mpvs.id"), nullable=False)
    mpv = relationship("MPVModel", back_populates="emendas")