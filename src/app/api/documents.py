from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from sqlalchemy.orm import Session
from src.app.db.models.documents import DocumentEmendaModel, MPVModel
from src.app.db.models.subjects import SubjectModel
from src.app.schemas.documents import (
    DocumentEmendaListResponse, 
    MPVResponse, 
    MPVCreate,
    DocumentEmendaResponse,
    DocumentEmendaCreate,
)
from src.app.ingestion.splitter import DocumentProcessor
from src.app.ingestion.convertor import converter
from src.app.service.classifier.classifier import ClassifierModel
from src.app.service.summarization.summarizer import summarize_file
from datetime import datetime
from src.app.db.session import get_db_session
import logging
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}}
)

async def create_document_processor(
    collection_name: str
):
    return DocumentProcessor(collection_name=collection_name)

@router.post("/upload_mpv", summary="Faz upload e cria nova MPV")
async def create_mpv(
    file: UploadFile = File(...),
    numero: int = Form(...),
    ano: int = Form(...),
    data_publicacao: datetime = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db_session)
):
    try:
        collection_name = f"mpv_{numero}_{ano}"

        file_text = converter.convert_file(file.file, file.filename)
        file_text = summarize_file(file_text)
        classifier = ClassifierModel(db)
        subjects = classifier.classify_file(file_text)

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

        # Busca os subjects pelo nome e cria a relação
        for subject_name in subjects:
            subject = db.query(SubjectModel).filter(SubjectModel.name == subject_name).first()
            if subject:
                document.subjects.append(subject)

        splitter = await create_document_processor(collection_name)
        processed_chunks = splitter.process_and_store_document(
            md_text=file_text, 
            doc_id=document.id, 
            filename=file.filename, 
            document_type="MPV", 
            subjects=subjects
        )

        db.commit()
        
        return {
            "mpv": f"{numero}/{ano}",
            "document_id": document.id,
            "message": f"{processed_chunks} chunks indexados na coleção '{collection_name}'"
        }
        
    except Exception as e:
        if 'document' in locals() and hasattr(document, 'id') and document.id:
            db.rollback()
            splitter.delete_document_from_vector_db(document.id)
        
        logger.error(f"Erro ao processar MPV {numero}/{ano}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar documento: {str(e)}")

@router.post("/upload_emenda", summary="Faz upload e cria nova emenda")
async def create_document(
    file: UploadFile = File(...),
    num_emenda: int = Form(...),
    apresentada_por: str = Form(...),
    data_apresentacao: datetime = Form(...),
    mpv_id: int = Form(..., description="ID da MPV associada à emenda"),
    db: Session = Depends(get_db_session)
):
    logger.info(f"Iniciando processamento da emenda {num_emenda}")
    
    try:
        mpv = db.query(MPVModel).filter(MPVModel.id == mpv_id).first()
        if not mpv:
            raise HTTPException(status_code=404, detail=f"MPV com ID {mpv_id} não encontrada")
        
        file_text = converter.convert_file(file.file, file.filename)
        classifier = ClassifierModel(db)
        subjects = classifier.classify_file(file_text)
        
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

        # Busca os subjects pelo nome e cria a relação
        for subject_name in subjects:
            subject = db.query(SubjectModel).filter(SubjectModel.name == subject_name).first()
            if subject:
                document.subjects.append(subject)

        splitter = await create_document_processor(mpv.collection_name)
        processed_chunks = splitter.process_and_store_document(
            md_text=file_text, 
            doc_id=document.id, 
            filename=file.filename, 
            document_type="EMENDA", 
            parent_id=mpv_id,
            subjects=subjects
        )
        
        db.commit()
        
        logger.info(f"Emenda {num_emenda} processada: {processed_chunks} chunks")
        
        return {
            "emenda": num_emenda,
            "document_id": document.id,
            "mpv": f"{mpv.numero}/{mpv.ano}",
            "message": f"{processed_chunks} chunks indexados na coleção '{mpv.collection_name}'"
        }
        
    except Exception as e:
        if 'document' in locals() and hasattr(document, 'id') and document.id:
            db.rollback()
            splitter.delete_document_from_vector_db(document.id)
        
        logger.error(f"Erro ao processar emenda {num_emenda}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar documento: {str(e)}")

@router.get("/", summary="Lista todos os documentos na coleção")
def list_documents(db: Session = Depends(get_db_session)):
    documents = db.query(MPVModel).all()
    return [MPVResponse.model_validate(document) for document in documents]

@router.get("/{doc_id}", summary="Lista MPV e emendas")
async def update_document(doc_id: int, db: Session = Depends(get_db_session)):
    mpv_document = db.query(MPVModel).filter(MPVModel.id == doc_id).first()
    emenda_document = db.query(DocumentEmendaModel).filter(DocumentEmendaModel.mpv_id == doc_id).all()
    if not mpv_document:
        raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' não encontrado")
    
    mpv_response = MPVResponse.model_validate(mpv_document)
    return DocumentEmendaListResponse(mpv_id=mpv_document.id, mpv=mpv_response, emendas=emenda_document)

@router.put("/{doc_id}", summary="Atualiza MPV")
async def update_document(doc_id: int, mpv_update: MPVCreate, db: Session = Depends(get_db_session)):
    mpv_document = db.query(MPVModel).filter(MPVModel.id == doc_id).first()
    if not mpv_document:
        raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' não encontrado")
    
    # Update MPV fields
    mpv_document.numero = mpv_update.numero
    mpv_document.ano = mpv_update.ano
    mpv_document.data_publicacao = mpv_update.data_publicacao
    mpv_document.status = mpv_update.status
    mpv_document.filename = mpv_update.filename
    mpv_document.collection_name = mpv_update.collection_name
    
    try:
        db.commit()
        # Convert to response model
        mpv_response = MPVResponse.model_validate(mpv_document)
        return mpv_response
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao atualizar MPV {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar documento: {str(e)}")

@router.delete("/{doc_id}", summary="Remove MPV e emendas")
async def delete_document(doc_id: int, db: Session = Depends(get_db_session)):
    try:
        # Verificar existência
        mpv_document = db.query(MPVModel).filter(MPVModel.id == doc_id).first()
        emenda_document = db.query(DocumentEmendaModel).filter(DocumentEmendaModel.mpv_id == doc_id).all()
        if not mpv_document:
            raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' não encontrado")
        
        splitter = await create_document_processor(mpv_document.collection_name)
        
        try:
            splitter.delete_document_from_vector_db(doc_id)
        except Exception as e:
            logger.error(f"Erro ao remover coleção '{mpv_document.collection_name}' do vector store: {str(e)}")
        
        # Delete from database
        for emenda in emenda_document:
            emenda_splitter = await create_document_processor(emenda.collection_name)
            emenda_splitter.delete_document_from_vector_db(emenda.id)
            db.delete(emenda)
        db.delete(mpv_document)
        db.commit()
        
        return {
            "doc_id": doc_id,
            "message": f"MPV e emendas removidos, coleção '{mpv_document.collection_name}' removida"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao deletar documento {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao deletar documento")

@router.put("/emenda/{doc_id}", summary="Atualiza uma emenda existente")
async def update_emenda(doc_id: int, emenda_update: DocumentEmendaCreate, db: Session = Depends(get_db_session)):
    try:
        emenda = db.query(DocumentEmendaModel).filter(DocumentEmendaModel.id == doc_id).first()
        if not emenda:
            raise HTTPException(status_code=404, detail=f"Emenda '{doc_id}' não encontrada")
        
        # Verificar se a MPV existe
        mpv = db.query(MPVModel).filter(MPVModel.id == emenda_update.mpv_id).first()
        if not mpv:
            raise HTTPException(status_code=404, detail=f"MPV com ID {emenda_update.mpv_id} não encontrada")
        
        # Atualizar campos
        emenda.num_emenda = emenda_update.num_emenda
        emenda.apresentada_por = emenda_update.apresentada_por
        emenda.data_apresentacao = emenda_update.data_apresentacao
        emenda.mpv_id = emenda_update.mpv_id
        emenda.filename = emenda_update.filename
        emenda.collection_name = emenda_update.collection_name
        
        db.commit()
        
        return DocumentEmendaResponse.model_validate(emenda)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao atualizar emenda {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar emenda: {str(e)}")

@router.delete("/emenda/{doc_id}", summary="Remove uma emenda")
async def delete_emenda(
    doc_id: int,
    db: Session = Depends(get_db_session)
):
    try:
        # Verificar existência
        emenda = db.query(DocumentEmendaModel).filter(DocumentEmendaModel.id == doc_id).first()
        if not emenda:
            raise HTTPException(status_code=404, detail=f"Emenda '{doc_id}' não encontrada")
        
        splitter = await create_document_processor(emenda.collection_name)
        splitter.delete_document_from_vector_db(emenda.id)
        
        db.delete(emenda)
        db.commit()
        
        return {
            "doc_id": doc_id,
            "message": f"Emenda removida"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao deletar emenda {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao deletar emenda")
    
@router.get("/emenda/{mpv_id}/{num_emenda}", summary="Obtém uma emenda específica")
async def get_emenda(mpv_id: int, num_emenda: int, db: Session = Depends(get_db_session)):
    emenda = db.query(DocumentEmendaModel).filter(DocumentEmendaModel.mpv_id == mpv_id, DocumentEmendaModel.num_emenda == num_emenda).first()
    if not emenda:
        raise HTTPException(status_code=404, detail=f"Emenda {num_emenda} da MPV {mpv_id} não encontrada")
    return DocumentEmendaResponse.model_validate(emenda)

@router.get("/emenda/{subject}", summary="Obtém uma emenda por assunto")
async def get_emenda_by_subject(subject: str, db: Session = Depends(get_db_session)):
    emendas = db.query(DocumentEmendaModel).filter(DocumentEmendaModel.subjects.any(SubjectModel.name == subject)).all()
    if not emendas:
        raise HTTPException(status_code=404, detail=f"Nenhuma emenda encontrada para o assunto '{subject}'")
    return [DocumentEmendaResponse.model_validate(emenda) for emenda in emendas]