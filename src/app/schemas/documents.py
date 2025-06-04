from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class SubjectResponse(BaseModel):
    id: int = Field(..., description="ID do subject")
    name: str = Field(..., description="Nome do subject")

    class Config:
        from_attributes = True

# Base schema with common fields
class DocumentBaseSchema(BaseModel):
    id: int = Field(..., description="ID do documento")
    filename: str = Field(..., description="Nome do arquivo")
    collection_name: str = Field(..., description="Nome da coleção")
    subjects: List[SubjectResponse] = Field(..., description="Assuntos do documento")
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data de atualização")

    class Config:
        from_attributes = True

# MPV schemas
class MPVResponse(DocumentBaseSchema):
    numero: int = Field(..., description="Número da MPV")
    ano: int = Field(..., description="Ano da MPV")
    data_publicacao: datetime = Field(..., description="Data de publicação da MPV")
    status: str = Field(..., description="Status da MPV")

class MPVCreate(BaseModel):
    numero: int = Field(..., description="Número da MPV")
    ano: int = Field(..., description="Ano da MPV")
    data_publicacao: datetime = Field(..., description="Data de publicação da MPV")
    status: str = Field(..., description="Status da MPV")
    filename: str = Field(..., description="Nome do arquivo")
    collection_name: str = Field(..., description="Nome da coleção")

# Document Emenda schemas
class DocumentEmendaResponse(DocumentBaseSchema):
    num_emenda: int = Field(..., description="Número da emenda")
    apresentada_por: str = Field(..., description="Quem apresentou a emenda")
    data_apresentacao: datetime = Field(..., description="Data de apresentação da emenda")
    chunks_count: int = Field(..., description="Número de chunks do documento")
    vector_store_name: Optional[str] = Field(None, description="Nome do vector store")
    mpv_id: int = Field(..., description="ID da MPV associada")

class DocumentEmendaCreate(BaseModel):
    num_emenda: int = Field(..., description="Número da emenda")
    apresentada_por: str = Field(..., description="Quem apresentou a emenda")
    data_apresentacao: datetime = Field(..., description="Data de apresentação da emenda")
    mpv_id: int = Field(..., description="ID da MPV associada à emenda")
    filename: str = Field(..., description="Nome do arquivo")
    collection_name: str = Field(..., description="Nome da coleção")

# Response schemas
class DocumentEmendaListResponse(BaseModel):
    mpv_id: int = Field(..., description="ID da MPV")
    mpv: MPVResponse = Field(..., description="MPV")
    emendas: List[DocumentEmendaResponse] = Field(..., description="Lista de documentos de emenda")

    class Config:
        from_attributes = True

class DocumentCreateResponse(BaseModel):
    doc_id: str = Field(..., description="Identificador único do documento")
    message: str = Field(..., description="Mensagem de confirmação da operação")

class DocumentListResponse(BaseModel):
    documents: List[str] = Field(..., description="Lista de IDs de documentos na coleção")

class DocumentChunksResponse(BaseModel):
    doc_id: str = Field(..., description="Identificador do documento")
    chunks: List[str] = Field(..., description="Lista de conteúdo dos chunks do documento")

class OperationResponse(BaseModel):
    doc_id: str = Field(..., description="Identificador do documento")
    message: str = Field(..., description="Mensagem de confirmação da operação")