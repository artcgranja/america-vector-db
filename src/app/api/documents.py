from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Form
from typing import List, Optional
from contextlib import contextmanager
from src.app.db.models.documents import DocumentEmendaModel, MPVModel
from src.app.schemas.documents import DocumentEmendaCreate
from src.app.ingestion.loader import load_document
from src.app.ingestion.splitter import split_document
from src.app.vectorization.vector_store import get_vector_store
from datetime import datetime
from src.app.db.session import get_db_session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}}
)

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

@router.post("/upload_mpv", summary="Faz upload e cria nova MPV")
async def create_mpv(
    file: UploadFile = File(...),
    numero: int = Form(...),
    ano: int = Form(...),
    data_publicacao: datetime = Form(...),
    status: str = Form(...)
):
  
    docs = await load_document(file)
    
    with get_db_session() as db:
        try:
            # Criar nome da coleção baseado no número e ano da MPV
            collection_name = f"mpv_{numero}_{ano}"
            
            document = MPVModel(
                filename=file.filename,
                collection_name=collection_name,
                numero=numero,
                ano=ano,
                data_publicacao=data_publicacao,
                status=status
            )
            
            db.add(document)
            db.flush()

            chunks = split_document(docs)
            
            metadata = {
                "doc_id": document.id,
                "source": file.filename,
            }

            if not chunks:
                raise HTTPException(status_code=400, detail="Nenhum chunk foi gerado do documento")
            
            prepare_chunks(chunks, document.id, metadata)
            vs = get_vector_store(collection_name)
            vs.add_documents(chunks)
            
            document.chunks_count = len(chunks)
            
            db.commit()
            
            logger.info(f"MPV {numero}/{ano} processada: {len(chunks)} chunks")
            
            return {
                "mpv": f"{numero}/{ano}",
                "document_id": document.id,
                "message": f"{len(chunks)} chunks indexados na coleção '{collection_name}'"
            }
            
        except Exception as e:
            if 'document' in locals() and hasattr(document, 'id') and document.id:
                db.rollback()
                cleanup_vector_store(collection_name, document.id)
            
            logger.error(f"Erro ao processar MPV {numero}/{ano}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Erro ao processar documento: {str(e)}")

@router.post("/upload_emenda", summary="Faz upload e cria novo documento na coleção")
async def create_document(
    file: UploadFile = File(...),
    num_emenda: int = Form(...),
    apresentada_por: str = Form(...),
    data_apresentacao: datetime = Form(...),
    mpv_id: int = Form(..., description="ID da MPV associada à emenda")
):
    logger.info(f"Iniciando processamento da emenda {num_emenda}")
    
    docs = await load_document(file)
    
    with get_db_session() as db:
        try:
            mpv = db.query(MPVModel).filter(MPVModel.id == mpv_id).first()
            if not mpv:
                raise HTTPException(status_code=404, detail=f"MPV com ID {mpv_id} não encontrada")
            
            document = DocumentEmendaModel(
                filename=file.filename,
                collection_name=mpv.collection_name,
                num_emenda=num_emenda,
                apresentada_por=apresentada_por,
                data_apresentacao=data_apresentacao,
                mpv_id=mpv_id
            )
            
            db.add(document)
            db.flush()

            metadata = {
                "doc_id": document.id,
                "source": file.filename,
                "num_emenda": num_emenda,
            }

            chunks = split_document(docs)
            
            if not chunks:
                raise HTTPException(status_code=400, detail="Nenhum chunk foi gerado do documento")
            
            prepare_chunks(chunks, document.id, metadata)
            vs = get_vector_store(mpv.collection_name)
            vs.add_documents(chunks)
            
            document.chunks_count = len(chunks)
            document.vector_store_name = mpv.collection_name
            
            db.commit()
            
            logger.info(f"Emenda {num_emenda} processada: {len(chunks)} chunks")
            
            return {
                "emenda": num_emenda,
                "document_id": document.id,
                "mpv": f"{mpv.numero}/{mpv.ano}",
                "message": f"{len(chunks)} chunks indexados na coleção '{mpv.collection_name}'"
            }
            
        except Exception as e:
            if 'document' in locals() and hasattr(document, 'id') and document.id:
                db.rollback()
                cleanup_vector_store(mpv.collection_name, document.id)
            
            logger.error(f"Erro ao processar emenda {num_emenda}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Erro ao processar documento: {str(e)}")

@router.get("/", summary="Lista todos os documentos na coleção")
def list_documents():
    with get_db_session() as db:
        documents = db.query(MPVModel).all()
        return documents

@router.get("/{doc_id}", summary="Recupera chunks de um documento específico")
def get_document(doc_id: int):
    try:
        with get_db_session() as db:
            document = db.query(DocumentEmendaModel).filter(DocumentEmendaModel.id == int(doc_id)).first()
            if not document:
                raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' não encontrado")
            
            return document
    except HTTPException:
        raise

@router.put("/{doc_id}", summary="Atualiza um documento existente")
async def update_document(doc_id: int):
    with get_db_session() as db:
        document = db.query(DocumentEmendaModel).filter(DocumentEmendaModel.id == int(doc_id)).first()
        if not document:
            raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' não encontrado")
        
        return document

@router.delete("/{doc_id}", summary="Remove um documento da coleção")
def delete_document(doc_id: int):
    with get_db_session() as db:
        try:
            # Verificar existência
            document = db.query(DocumentEmendaModel).filter(DocumentEmendaModel.id == int(doc_id)).first()
            if not document:
                raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' não encontrado")
            
            # Remover do vector store e banco
            vs = get_vector_store(document.collection_name)
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