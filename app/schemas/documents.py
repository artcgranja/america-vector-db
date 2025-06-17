from typing import List, Optional, Dict
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
    summary: str = Field(..., description="Resumo do documento")
    subjects: List[SubjectResponse] = Field(..., description="Assuntos do documento")
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data de atualização")
    document_type: str = Field(..., description="Tipo do documento")
    document_year: int = Field(..., description="Ano do documento")
    presented_by: str = Field(..., description="Quem apresentou o documento")
    central_theme: str = Field(..., description="Tema central do documento")
    link: str = Field(..., description="Link para o documento")

    class Config:
        from_attributes = True

# MPV schemas
class PrimaryDocumentResponse(DocumentBaseSchema):
    document_number: int = Field(..., description="Número da MPV")
    document_name: str = Field(..., description="Nome da MPV")
    presented_at: datetime = Field(..., description="Data de apresentação da MPV")
    key_points: Dict[str, str] = Field(..., description="Pontos chave do documento")
    collection_name: str = Field(..., description="Nome da coleção")

class PrimaryDocumentCreate(BaseModel):
    document_number: int = Field(..., description="Número da MPV")
    document_year: int = Field(..., description="Ano da MPV")
    presented_at: datetime = Field(..., description="Data de apresentação da MPV")
    document_type: str = Field(..., description="Tipo do documento")
    presented_by: str = Field(..., description="Quem apresentou o documento")
    filename: str = Field(..., description="Nome do arquivo")
    collection_name: str = Field(..., description="Nome da coleção")
    summary: str = Field(..., description="Resumo do documento")
    central_theme: str = Field(..., description="Tema central do documento")
    link: str = Field(..., description="Link para o documento")
    key_points: Dict[str, str] = Field(..., description="Pontos chave do documento")

# Document Emenda schemas
class SecondaryDocumentResponse(DocumentBaseSchema):
    role: str = Field(..., description="Papel do apresentador")
    party_affiliation: str = Field(..., description="Afiliação partidária")
    primary_id: int = Field(..., description="ID do documento principal associado")
    document_number: int = Field(..., description="Número do documento")
    document_name: str = Field(..., description="Nome do documento")
    presented_at: datetime = Field(..., description="Data de apresentação")
    key_points: Dict[str, str] = Field(..., description="Pontos chave do documento")

    class Config:
        from_attributes = True

class SecondaryDocumentCreate(BaseModel):
    filename: str = Field(..., description="Nome do arquivo")
    document_type: str = Field(..., description="Tipo do documento")
    document_number: int = Field(..., description="Número do documento")
    document_year: int = Field(..., description="Ano do documento")
    document_name: str = Field(..., description="Nome do documento")
    presented_by: str = Field(..., description="Quem apresentou o documento")
    presented_at: datetime = Field(..., description="Data de apresentação")
    summary: str = Field(..., description="Resumo do documento")
    central_theme: str = Field(..., description="Tema central do documento")
    key_points: Dict[str, str] = Field(..., description="Pontos chave do documento")
    link: str = Field(..., description="Link para o documento")
    role: str = Field(..., description="Papel do apresentador")
    party_affiliation: str = Field(..., description="Afiliação partidária")
    primary_id: int = Field(..., description="ID do documento principal associado")

# Response schemas
class SecondaryDocumentListResponse(BaseModel):
    primary_id: int = Field(..., description="ID da MPV")
    primary: PrimaryDocumentResponse = Field(..., description="MPV")
    secondaries: List[SecondaryDocumentResponse] = Field(..., description="Lista de documentos de emenda")

    class Config:
        from_attributes = True

class SecondaryDocumentCreateResponse(BaseModel):
    doc_id: str = Field(..., description="Identificador único do documento")
    message: str = Field(..., description="Mensagem de confirmação da operação")

class SecondaryDocumentListResponse(BaseModel):
    documents: List[str] = Field(..., description="Lista de IDs de documentos na coleção")

class SecondaryDocumentChunksResponse(BaseModel):
    doc_id: str = Field(..., description="Identificador do documento")
    chunks: List[str] = Field(..., description="Lista de conteúdo dos chunks do documento")

class SecondaryDocumentOperationResponse(BaseModel):
    doc_id: str = Field(..., description="Identificador do documento")
    message: str = Field(..., description="Mensagem de confirmação da operação")