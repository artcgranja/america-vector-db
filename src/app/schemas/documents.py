from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentCreateResponse(BaseModel):
    doc_id: str = Field(..., description="Identificador único do documento")
    message: str = Field(..., description="Mensagem de confirmação da operação")

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DocumentEmendaCreate(BaseModel):
    """
    Schema para criação de um documento de emenda com metadados.
    O upload do arquivo deve ser feito via UploadFile no endpoint.
    """
    num_emenda: int = Field(..., description="Número da emenda")
    apresentada_por: str = Field(..., description="Quem apresentou a emenda")
    data_apresentacao: datetime = Field(..., description="Data de apresentação da emenda")
    collection_name: Optional[str] = Field(
        None, description="Nome da coleção de vetores onde o documento será indexado"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "num_emenda": 505,
                "apresentada_por": "Deputado Fulano",
                "data_apresentacao": "2025-05-29T00:00:00Z",
                "collection_name": "emendas_2025"
            }
        }


class DocumentListResponse(BaseModel):
    documents: List[str] = Field(..., description="Lista de IDs de documentos na coleção")


class DocumentChunksResponse(BaseModel):
    doc_id: str = Field(..., description="Identificador do documento")
    chunks: List[str] = Field(..., description="Lista de conteúdo dos chunks do documento")


class OperationResponse(BaseModel):
    doc_id: str = Field(..., description="Identificador do documento")
    message: str = Field(..., description="Mensagem de confirmação da operação")