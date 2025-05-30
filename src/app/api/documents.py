from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Form
from typing import List, Optional
from contextlib import contextmanager
from app.db.models.documents import DocumentEmendaModel
from app.schemas.documents import DocumentEmendaCreate
from app.ingestion.loader import load_document
from app.ingestion.splitter import split_document
from app.vectorization.vector_store import get_vector_store
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.db.session import SessionLocal
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}}
)

# Context manager para gerenciar transações
@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Helper para cleanup do vector store
def cleanup_vector_store(collection_name: str, doc_id: int):
    """Remove chunks do vector store em caso de erro"""
    try:
        vs = get_vector_store(collection_name)
        vs.delete(filter={"doc_id": str(doc_id)})
        logger.info(f"Chunks removidos do vector store para documento {doc_id}")
    except Exception as e:
        logger.error(f"Erro ao remover chunks do vector store: {str(e)}")

# Helper para preparar chunks
def prepare_chunks(chunks, document_id: int, metadata: dict):
    """Adiciona metadados aos chunks"""
    for chunk in chunks:
        chunk.metadata.update({
            'doc_id': document_id,
            **metadata
        })
    return chunks

@router.post("/upload_emenda", summary="Faz upload e cria novo documento na coleção")
async def create_document(
    file: UploadFile = File(...),
    num_emenda: int = Form(...),
    apresentada_por: str = Form(...),
    data_apresentacao: datetime = Form(...),
    collection_name: Optional[str] = Query(None, description="Nome da coleção de vetores")
):
    logger.info(f"Iniciando processamento da emenda {num_emenda}")
    
    # Processar arquivo primeiro (mais provável de falhar)
    docs = await load_document(file)
    chunks = split_document(docs)
    
    if not chunks:
        raise HTTPException(status_code=400, detail="Nenhum chunk foi gerado do documento")
    
    # Preparar metadados
    metadata = {
        "num_emenda": num_emenda,
        "apresentada_por": apresentada_por,
        "data_apresentacao": data_apresentacao.isoformat() if isinstance(data_apresentacao, datetime) else str(data_apresentacao)
    }
    
    with get_db_session() as db:
        try:
            # Criar documento
            document = DocumentEmendaModel(
                filename=file.filename,
                collection_name=collection_name,
                num_emenda=num_emenda,
                apresentada_por=apresentada_por,
                data_apresentacao=data_apresentacao,
                document_metadata=metadata
            )
            
            db.add(document)
            db.flush()  # Gera ID
            
            # Preparar e adicionar chunks
            prepare_chunks(chunks, document.id, metadata)
            vs = get_vector_store(collection_name)
            vs.add_documents(chunks)
            
            # Finalizar documento
            document.chunks_count = len(chunks)
            document.vector_store_name = collection_name or vs.collection_name
            
            db.commit()
            
            logger.info(f"Emenda {num_emenda} processada: {len(chunks)} chunks")
            
            return {
                "emenda": num_emenda,
                "document_id": document.id,
                "message": f"{len(chunks)} chunks indexados na coleção '{document.vector_store_name}'"
            }
            
        except Exception as e:
            # Cleanup automático do vector store se necessário
            if 'document' in locals() and hasattr(document, 'id') and document.id:
                cleanup_vector_store(collection_name, document.id)
            
            logger.error(f"Erro ao processar emenda {num_emenda}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Erro ao processar documento: {str(e)}")

@router.get("/", summary="Lista todos os documentos na coleção")
def list_documents(collection_name: Optional[str] = Query(None)):
    try:
        vs = get_vector_store(collection_name)
        all_chunks = vs.get_all_documents()
        doc_ids = list({chunk.metadata.get('doc_id') for chunk in all_chunks if 'doc_id' in chunk.metadata})
        return {"documents": doc_ids}
    except Exception as e:
        logger.error(f"Erro ao listar documentos: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao listar documentos")

@router.get("/{doc_id}", summary="Recupera chunks de um documento específico")
def get_document(doc_id: str, collection_name: Optional[str] = Query(None)):
    try:
        vs = get_vector_store(collection_name)
        all_chunks = vs.get_all_documents()
        chunks = [chunk.page_content for chunk in all_chunks if chunk.metadata.get('doc_id') == doc_id]
        
        if not chunks:
            raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' não encontrado")
            
        return {"doc_id": doc_id, "chunks": chunks}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao recuperar documento {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao recuperar documento")

@router.put("/{doc_id}", summary="Atualiza um documento existente")
async def update_document(
    doc_id: str,
    file: UploadFile = File(...),
    collection_name: Optional[str] = Query(None)
):
    # Processar arquivo primeiro
    docs = await load_document(file)
    chunks = split_document(docs)
    
    if not chunks:
        raise HTTPException(status_code=400, detail="Nenhum chunk foi gerado do novo documento")
    
    with get_db_session() as db:
        try:
            # Verificar existência
            document = db.query(DocumentEmendaModel).filter(DocumentEmendaModel.id == int(doc_id)).first()
            if not document:
                raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' não encontrado")
            
            vs = get_vector_store(collection_name)
            
            # Remover chunks antigos e adicionar novos
            vs.delete(filter={"doc_id": doc_id})
            
            metadata = {
                "num_emenda": document.num_emenda,
                "apresentada_por": document.apresentada_por,
                "data_apresentacao": document.data_apresentacao.isoformat()
            }
            
            prepare_chunks(chunks, int(doc_id), metadata)
            vs.add_documents(chunks)
            
            # Atualizar documento
            document.filename = file.filename
            document.chunks_count = len(chunks)
            document.updated_at = datetime.now()
            
            db.commit()
            
            return {"doc_id": doc_id, "message": f"Documento atualizado com {len(chunks)} chunks"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao atualizar documento {doc_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Erro ao atualizar documento")

@router.delete("/{doc_id}", summary="Remove um documento da coleção")
def delete_document(doc_id: str, collection_name: Optional[str] = Query(None)):
    with get_db_session() as db:
        try:
            # Verificar existência
            document = db.query(DocumentEmendaModel).filter(DocumentEmendaModel.id == int(doc_id)).first()
            if not document:
                raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' não encontrado")
            
            # Remover do vector store e banco
            vs = get_vector_store(collection_name)
            deleted_chunks = vs.delete(filter={"doc_id": doc_id})
            
            db.delete(document)
            db.commit()
            
            chunks_count = len(deleted_chunks) if deleted_chunks else 0
            return {"doc_id": doc_id, "message": f"Documento removido, {chunks_count} chunks deletados"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao deletar documento {doc_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Erro ao deletar documento")