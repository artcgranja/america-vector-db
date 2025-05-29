from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import List, Optional
import uuid
from app.ingestion.loader import load_document
from app.ingestion.splitter import split_document
from app.vectorization.vector_store import get_vector_store

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}}
)

@router.post("/upload", summary="Faz upload e cria novo documento na coleção")
async def create_document(
    file: UploadFile = File(...),
    collection_name: Optional[str] = Query(None, description="Nome da coleção de vetores")
):
    # Gera ID único para o documento
    doc_id = uuid.uuid4().hex
    # Carrega e divide
    docs = await load_document(file)
    chunks = split_document(docs)
    # Adiciona metadata de doc_id em cada chunk
    for chunk in chunks:
        chunk.metadata['doc_id'] = doc_id
    # Vetoriza e armazena na coleção
    vs = get_vector_store(collection_name)
    vs.add_documents(chunks)
    return {"doc_id": doc_id, "message": f"{len(chunks)} chunks indexados na coleção '{collection_name or vs.collection_name}'"}

@router.get("/documents", summary="Lista todos os documentos na coleção")
def list_documents(
    collection_name: Optional[str] = Query(None, description="Nome da coleção de vetores")
):
    vs = get_vector_store(collection_name)
    all_chunks = vs.get_all_documents()
    doc_ids = list({chunk.metadata.get('doc_id') for chunk in all_chunks if 'doc_id' in chunk.metadata})
    return {"documents": doc_ids}

@router.get("/documents/{doc_id}", summary="Recupera chunks de um documento específico")
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

@router.put("/documents/{doc_id}", summary="Atualiza um documento existente")
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

@router.delete("/documents/{doc_id}", summary="Remove um documento da coleção")
def delete_document(
    doc_id: str,
    collection_name: Optional[str] = Query(None, description="Nome da coleção de vetores")
):
    vs = get_vector_store(collection_name)
    deleted = vs.delete(filter={"doc_id": doc_id})
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' não encontrado")
    return {"doc_id": doc_id, "message": f"Documento '{doc_id}' removido, {len(deleted)} chunks deletados"}