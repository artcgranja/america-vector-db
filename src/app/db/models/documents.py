from sqlalchemy import Column, String, DateTime, JSON, func, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DocumentBaseModel(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    collection_name = Column(String, nullable=False)
    document_metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, filename={self.filename})>"

class DocumentEmendaModel(DocumentBaseModel):
    __tablename__ = "document_emendas"

    num_emenda = Column(Integer, nullable=False)
    apresentada_por = Column(String, nullable=False)
    data_apresentacao = Column(DateTime(timezone=True), nullable=False)
    chunks_count = Column(Integer, default=0)
    vector_store_name = Column(String, nullable=True)