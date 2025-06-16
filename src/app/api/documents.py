from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from sqlalchemy.orm import Session
from src.app.db.models.documents import PrimaryDocumentModel, SecondaryDocumentModel
from src.app.db.models.subjects import SubjectModel
from src.app.schemas.documents import (
    PrimaryDocumentListResponse, 
    PrimaryDocumentResponse, 
    PrimaryDocumentCreate,
    SecondaryDocumentResponse,
    SecondaryDocumentCreate,
    DocumentListResponse,
)
from src.app.ingestion.splitter import DocumentProcessor
from src.app.ingestion.convertor import converter
from app.service.classifier.subjects_classifier import ClassifierModel
from src.app.service.summarization.summaryzer import SummaryzerModel
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

@router.post("/upload_primary", summary="Faz upload e cria nova MPV")
async def create_primary(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    document_name: str = Form(...),
    presented_by: str = Form(...),
    presented_at: datetime = Form(...),
    db: Session = Depends(get_db_session)
):
    try:
        collection_name = f"{document_type}_{document_name}"

        file_text = converter.convert_file(file.file, file.filename)
        classifier = ClassifierModel(db)
        summaryzer = SummaryzerModel(db)
        subjects = classifier.classify_file(file_text)
        summary = summaryzer.summarize_markdown_file(file_text)

        document = PrimaryDocumentModel(
            filename=file.filename,
            document_type=document_type,
            collection_name=collection_name,
            summary=summary,
            document_name=document_name,
            presented_by=presented_by,
            presented_at=presented_at
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
            "document_name": document_name,
            "document_id": document.id,
            "message": f"{processed_chunks} chunks indexados na coleção '{collection_name}'"
        }
        
    except Exception as e:
        if 'document' in locals() and hasattr(document, 'id') and document.id:
            db.rollback()
            splitter.delete_document_from_vector_db(document.id)
        
        logger.error(f"Erro ao processar MPV {document_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar documento: {str(e)}")

@router.post("/upload_secondary", summary="Faz upload e cria nova emenda")
async def create_secondary(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    document_name: str = Form(...),
    presented_by: str = Form(...),
    presented_at: datetime = Form(...),
    primary_id: int = Form(..., description="ID da MPV associada à emenda"),
    party_affiliation: str = Form(..., description="Partido político do autor da emenda"),
    db: Session = Depends(get_db_session)
):
    logger.info(f"Iniciando processamento do documento secundário {document_name}")
    
    try:
        primary = db.query(PrimaryDocumentModel).filter(PrimaryDocumentModel.id == primary_id).first()
        if not primary:
            raise HTTPException(status_code=404, detail=f"Documento primário com ID {primary_id} não encontrado")
        
        file_text = converter.convert_file(file.file, file.filename)
        classifier = ClassifierModel(db)
        summaryzer = SummaryzerModel(db)
        subjects = classifier.classify_file(file_text)
        summary = summaryzer.summarize_markdown_file(file_text, primary.summary)
        
        document = SecondaryDocumentModel(
            filename=file.filename,
            document_type=document_type,
            document_name=document_name,
            collection_name=primary.collection_name,
            presented_by=presented_by,
            presented_at=presented_at,
            summary=summary,
            party_affiliation=party_affiliation,
            primary_id=primary_id
        )
        
        db.add(document)
        db.flush()

        # Busca os subjects pelo nome e cria a relação
        for subject_name in subjects:
            subject = db.query(SubjectModel).filter(SubjectModel.name == subject_name).first()
            if subject:
                document.subjects.append(subject)

        splitter = await create_document_processor(primary.collection_name)
        processed_chunks = splitter.process_and_store_document(
            md_text=file_text, 
            doc_id=document.id, 
            filename=file.filename, 
            document_type=document_type, 
            parent_id=primary_id,
            subjects=subjects
        )
        
        db.commit()
        
        logger.info(f"Documento secundário {document_name} processado: {processed_chunks} chunks")
        
        return {
            "document_name": document_name,
            "document_id": document.id,
            "primary_document": primary.document_name,
            "message": f"{processed_chunks} chunks indexados na coleção '{primary.collection_name}'"
        }
        
    except Exception as e:
        if 'document' in locals() and hasattr(document, 'id') and document.id:
            db.rollback()
            splitter.delete_document_from_vector_db(document.id)
        
        logger.error(f"Erro ao processar documento secundário {document_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar documento: {str(e)}")

@router.get("/", summary="Lista todos os documentos na coleção")
def list_documents(db: Session = Depends(get_db_session)):
    documents = db.query(PrimaryDocumentModel).all()
    return [PrimaryDocumentResponse.model_validate(document) for document in documents]

@router.get("/{doc_id}", summary="Lista documento primário e secundários")
async def get_document(doc_id: int, db: Session = Depends(get_db_session)):
    primary_document = db.query(PrimaryDocumentModel).filter(PrimaryDocumentModel.id == doc_id).first()
    secondary_documents = db.query(SecondaryDocumentModel).filter(SecondaryDocumentModel.primary_id == doc_id).all()
    if not primary_document:
        raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' não encontrado")
    
    primary_response = PrimaryDocumentResponse.model_validate(primary_document)
    return DocumentListResponse(primary_id=primary_document.id, primary=primary_response, secondary_documents=secondary_documents)

@router.put("/{doc_id}", summary="Atualiza documento primário")
async def update_document(doc_id: int, document_update: PrimaryDocumentCreate, db: Session = Depends(get_db_session)):
    primary_document = db.query(PrimaryDocumentModel).filter(PrimaryDocumentModel.id == doc_id).first()
    if not primary_document:
        raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' não encontrado")
    
    # Update document fields
    primary_document.document_type = document_update.document_type
    primary_document.document_name = document_update.document_name
    primary_document.presented_by = document_update.presented_by
    primary_document.presented_at = document_update.presented_at
    primary_document.filename = document_update.filename
    primary_document.summary = document_update.summary
    primary_document.collection_name = document_update.collection_name
    
    try:
        db.commit()
        # Convert to response model
        primary_response = PrimaryDocumentResponse.model_validate(primary_document)
        return primary_response
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao atualizar documento {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar documento: {str(e)}")

@router.delete("/{doc_id}", summary="Remove documento primário e secundários")
async def delete_document(doc_id: int, db: Session = Depends(get_db_session)):
    try:
        # Verificar existência
        primary_document = db.query(PrimaryDocumentModel).filter(PrimaryDocumentModel.id == doc_id).first()
        secondary_documents = db.query(SecondaryDocumentModel).filter(SecondaryDocumentModel.primary_id == doc_id).all()
        if not primary_document:
            raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' não encontrado")
        
        splitter = await create_document_processor(primary_document.collection_name)
        
        try:
            splitter.delete_document_from_vector_db(doc_id)
        except Exception as e:
            logger.error(f"Erro ao remover coleção '{primary_document.collection_name}' do vector store: {str(e)}")
        
        # Delete from database
        for secondary in secondary_documents:
            secondary_splitter = await create_document_processor(secondary.collection_name)
            secondary_splitter.delete_document_from_vector_db(secondary.id)
            db.delete(secondary)
        db.delete(primary_document)
        db.commit()
        
        return {
            "doc_id": doc_id,
            "message": f"Documento primário e secundários removidos, coleção '{primary_document.collection_name}' removida"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao deletar documento {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao deletar documento")

@router.put("/secondary/{doc_id}", summary="Atualiza um documento secundário existente")
async def update_secondary(doc_id: int, secondary_update: SecondaryDocumentCreate, db: Session = Depends(get_db_session)):
    try:
        secondary = db.query(SecondaryDocumentModel).filter(SecondaryDocumentModel.id == doc_id).first()
        if not secondary:
            raise HTTPException(status_code=404, detail=f"Documento secundário '{doc_id}' não encontrado")
        
        # Verificar se o documento primário existe
        primary = db.query(PrimaryDocumentModel).filter(PrimaryDocumentModel.id == secondary_update.primary_id).first()
        if not primary:
            raise HTTPException(status_code=404, detail=f"Documento primário com ID {secondary_update.primary_id} não encontrado")
        
        # Atualizar campos
        secondary.document_type = secondary_update.document_type
        secondary.document_name = secondary_update.document_name
        secondary.presented_by = secondary_update.presented_by
        secondary.presented_at = secondary_update.presented_at
        secondary.primary_id = secondary_update.primary_id
        secondary.filename = secondary_update.filename
        secondary.collection_name = secondary_update.collection_name
        secondary.party_affiliation = secondary_update.party_affiliation
        
        db.commit()
        
        return SecondaryDocumentResponse.model_validate(secondary)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao atualizar documento secundário {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar documento secundário: {str(e)}")

@router.delete("/secondary/{doc_id}", summary="Remove um documento secundário")
async def delete_secondary(
    doc_id: int,
    db: Session = Depends(get_db_session)
):
    try:
        # Verificar existência
        secondary = db.query(SecondaryDocumentModel).filter(SecondaryDocumentModel.id == doc_id).first()
        if not secondary:
            raise HTTPException(status_code=404, detail=f"Documento secundário '{doc_id}' não encontrado")
        
        splitter = await create_document_processor(secondary.collection_name)
        splitter.delete_document_from_vector_db(secondary.id)
        
        db.delete(secondary)
        db.commit()
        
        return {
            "doc_id": doc_id,
            "message": f"Documento secundário removido"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao deletar documento secundário {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao deletar documento secundário")
    
@router.get("/secondary/{primary_id}/{document_name}", summary="Obtém um documento secundário específico")
async def get_secondary(primary_id: int, document_name: str, db: Session = Depends(get_db_session)):
    secondary = db.query(SecondaryDocumentModel).filter(
        SecondaryDocumentModel.primary_id == primary_id, 
        SecondaryDocumentModel.document_name == document_name
    ).first()
    if not secondary:
        raise HTTPException(status_code=404, detail=f"Documento secundário {document_name} do documento primário {primary_id} não encontrado")
    return SecondaryDocumentResponse.model_validate(secondary)

@router.get("/secondary/subject/{subject}", summary="Obtém documentos secundários por assunto")
async def get_secondary_by_subject(subject: str, db: Session = Depends(get_db_session)):
    secondary_documents = db.query(SecondaryDocumentModel).filter(
        SecondaryDocumentModel.subjects.any(SubjectModel.name == subject)
    ).all()
    if not secondary_documents:
        raise HTTPException(status_code=404, detail=f"Nenhum documento secundário encontrado para o assunto '{subject}'")
    return [SecondaryDocumentResponse.model_validate(doc) for doc in secondary_documents]