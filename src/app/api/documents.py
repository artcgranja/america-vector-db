from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Form
from typing import List, Optional
from app.db.models.documents import DocumentEmendaModel
from app.schemas.documents import DocumentEmendaCreate
from app.ingestion.loader import load_document
from app.ingestion.splitter import split_document
from app.vectorization.vector_store import get_vector_store
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}}
)

@router.post("/upload_emenda", summary="Faz upload e cria novo documento na coleção")
async def create_document(
    file: UploadFile = File(...),
    num_emenda: int = Form(...),
    apresentada_por: str = Form(...),
    data_apresentacao: datetime = Form(...),
    collection_name: Optional[str] = Query(None, description="Nome da coleção de vetores")
):  
    filename = file.filename
    document = DocumentEmendaModel(
        filename=filename,
        collection_name=collection_name,
        num_emenda=num_emenda,
        apresentada_por=apresentada_por,
        data_apresentacao=data_apresentacao,
        metadata={
            "num_emenda": num_emenda,
            "apresentada_por": apresentada_por,
            "data_apresentacao": data_apresentacao
        }
    )
    docs = await load_document(file)
    chunks = split_document(docs)

    for chunk in chunks:
        chunk.metadata['num_emenda'] = num_emenda
        chunk.metadata['apresentada_por'] = apresentada_por
        chunk.metadata['data_apresentacao'] = data_apresentacao
    
    vs = get_vector_store(collection_name)
    vs.add_documents(chunks)
    
    # Atualiza o documento com informações do processamento
    document.chunks_count = len(chunks)
    document.vector_store_name = collection_name or vs.collection_name
    
    # Salva no banco de dados
    db = SessionLocal()
    try:
        db.add(document)
        db.commit()
        db.refresh(document)
    finally:
        db.close()
    
    return {
        "emenda": num_emenda, 
        "message": f"{len(chunks)} chunks indexados na coleção '{collection_name or vs.collection_name}'"
    }

@router.get("/", summary="Lista todos os documentos na coleção")
def list_documents(
    collection_name: Optional[str] = Query(None, description="Nome da coleção de vetores")
):
    vs = get_vector_store(collection_name)
    all_chunks = vs.get_all_documents()
    doc_ids = list({chunk.metadata.get('doc_id') for chunk in all_chunks if 'doc_id' in chunk.metadata})
    return {"documents": doc_ids}

@router.get("/{doc_id}", summary="Recupera chunks de um documento específico")
def get_document(
    doc_id: str,
    collection_name: Optional[str] = Query(None, description="Nome da coleção de vetores")
):
    vs = get_vector_store(collection_name)
    all_chunks = vs.get_all_documents()
    chunks = [chunk.page_content for chunk in all_chunks if chunk.metadata.get('doc_id') == doc_id]
    if not chunks:
        raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' não encontrado")
    return {"doc_id": doc_id, "chunks": chunks}

@router.put("/{doc_id}", summary="Atualiza um documento existente")
async def update_document(
    doc_id: str,
    file: UploadFile = File(...),
    collection_name: Optional[str] = Query(None, description="Nome da coleção de vetores")
):
    vs = get_vector_store(collection_name)
    # Remove chunks existentes do documento
    vs.delete(filter={"doc_id": doc_id})
    # Re-indexa novo arquivo
    docs = await load_document(file)
    chunks = split_document(docs)
    for chunk in chunks:
        chunk.metadata['doc_id'] = doc_id
    vs.add_documents(chunks)
    return {"doc_id": doc_id, "message": f"Documento '{doc_id}' atualizado com {len(chunks)} chunks"}

@router.delete("/{doc_id}", summary="Remove um documento da coleção")
def delete_document(
    doc_id: str,
    collection_name: Optional[str] = Query(None, description="Nome da coleção de vetores")
):
    vs = get_vector_store(collection_name)
    deleted = vs.delete(filter={"doc_id": doc_id})
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' não encontrado")
    return {"doc_id": doc_id, "message": f"Documento '{doc_id}' removido, {len(deleted)} chunks deletados"}