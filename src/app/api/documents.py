from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from sqlalchemy.orm import Session
from src.app.db.models.documents import PrimaryDocumentModel, SecondaryDocumentModel
from src.app.db.models.subjects import SubjectModel
from src.app.schemas.documents import (
    PrimaryDocumentResponse, 
    SecondaryDocumentListResponse,
)
from src.app.ingestion.splitter import DocumentProcessor
from src.app.service.workflow import document_workflow
from datetime import datetime
from src.app.db.session import get_db_session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}}
)

async def create_document_processor(collection_name: str):
    return DocumentProcessor(collection_name=collection_name)

@router.post("/upload_primary", summary="Faz upload e cria documento primário")
async def create_primary(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    document_name: str = Form(...),
    presented_by: str = Form(...),
    presented_at: datetime = Form(...),
    db: Session = Depends(get_db_session)
):
    logger.info(f"Iniciando processamento do documento primário {document_name}")
    
    try:
        collection_name = f"{document_type}_{document_name}"
        
        # Preparar metadados para o workflow
        metadata = {
            "document_type": document_type,
            "document_name": document_name,
            "presented_by": presented_by,
            "presented_at": presented_at,
            "collection_name": collection_name
            # Sem primary_id = documento primário
        }
        
        # 🚀 EXECUTAR WORKFLOW COMPLETO
        workflow_result = await document_workflow.process_document(
            file=file,
            filename=file.filename,
            metadata=metadata,
            db_session=db
        )
        
        # Verificar se o workflow foi bem-sucedido
        if workflow_result["processing_status"] == "error":
            logger.error(f"Erro no workflow: {workflow_result['error_message']}")
            raise HTTPException(status_code=500, detail=workflow_result["error_message"])
        
        # Verificar se documento é irrelevante
        if workflow_result["processing_status"] == "irrelevant":
            logger.warning(f"Documento {document_name} marcado como irrelevante")
            return {
                "document_name": document_name,
                "status": "irrelevant",
                "relevance_score": workflow_result["relevance_score"],
                "reason": workflow_result["irrelevance_reasons"][0] if workflow_result["irrelevance_reasons"] else "Não relacionado ao mercado de energia",
                "message": "Documento processado mas marcado como irrelevante"
            }
        
        # Criar documento no banco com resultados do workflow
        document = PrimaryDocumentModel(
            filename=file.filename,
            document_type=document_type,
            collection_name=collection_name,
            summary=workflow_result["summary"],
            central_theme=workflow_result["central_theme"],
            key_points=workflow_result["key_points"],
            document_name=document_name,
            presented_by=presented_by,
            presented_at=presented_at
        )
        
        db.add(document)
        db.flush()  # Para obter o ID
        
        # Associar subjects identificados pelo workflow
        for subject_name in workflow_result["subjects"]:
            subject = db.query(SubjectModel).filter(SubjectModel.name == subject_name).first()
            if subject:
                document.subjects.append(subject)
        
        # Processar e armazenar chunks no vector store
        splitter = await create_document_processor(collection_name)
        processed_chunks = splitter.process_and_store_document(
            md_text=workflow_result["text_content"], 
            doc_id=document.id, 
            filename=file.filename, 
            document_type=document_type,
            subjects=workflow_result["subjects"]
        )
        
        db.commit()
        
        logger.info(f"Documento primário {document_name} processado com sucesso")
        
        return {
            "document_name": document_name,
            "document_id": document.id,
            "processing_status": workflow_result["processing_status"],
            "subjects": workflow_result["subjects"],
            "central_theme": workflow_result["central_theme"],
            "key_points": workflow_result["key_points"],
            "relevance_score": workflow_result["relevance_score"],
            "chunks_processed": processed_chunks,
            "message": f"{processed_chunks} chunks indexados na coleção '{collection_name}'"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Cleanup em caso de erro
        if 'document' in locals() and hasattr(document, 'id') and document.id:
            db.rollback()
            try:
                splitter = await create_document_processor(collection_name)
                splitter.delete_document_from_vector_db(document.id)
            except:
                pass  # Falha no cleanup não deve quebrar o erro principal
        
        logger.error(f"Erro ao processar documento primário {document_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar documento: {str(e)}")

@router.post("/upload_secondary", summary="Faz upload e cria documento secundário")
async def create_secondary(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    document_name: str = Form(...),
    presented_by: str = Form(...),
    presented_at: datetime = Form(...),
    primary_id: int = Form(..., description="ID do documento primário"),
    role: str = Form(..., description="Cargo do autor"),
    party_affiliation: str = Form(..., description="Partido político do autor"),
    db: Session = Depends(get_db_session)
):
    logger.info(f"Iniciando processamento do documento secundário {document_name}")
    
    try:
        # Verificar se documento primário existe
        primary = db.query(PrimaryDocumentModel).filter(PrimaryDocumentModel.id == primary_id).first()
        if not primary:
            raise HTTPException(status_code=404, detail=f"Documento primário com ID {primary_id} não encontrado")
        
        # Preparar metadados para o workflow
        metadata = {
            "document_type": document_type,
            "document_name": document_name,
            "presented_by": presented_by,
            "presented_at": presented_at,
            "role": role,
            "party_affiliation": party_affiliation,
            "primary_id": primary_id,  # Indica que é documento secundário
            "collection_name": primary.collection_name
        }
        
        # 🚀 EXECUTAR WORKFLOW COMPLETO
        workflow_result = await document_workflow.process_document(
            file=file,
            filename=file.filename,
            metadata=metadata,
            db_session=db
        )
        
        # Verificar se o workflow foi bem-sucedido
        if workflow_result["processing_status"] == "error":
            logger.error(f"Erro no workflow: {workflow_result['error_message']}")
            raise HTTPException(status_code=500, detail=workflow_result["error_message"])
        
        # Verificar se documento é irrelevante
        if workflow_result["processing_status"] == "irrelevant":
            logger.warning(f"Documento secundário {document_name} marcado como irrelevante")
            return {
                "document_name": document_name,
                "status": "irrelevant", 
                "primary_document": primary.document_name,
                "relevance_score": workflow_result["relevance_score"],
                "reason": workflow_result["irrelevance_reasons"][0] if workflow_result["irrelevance_reasons"] else "Não relacionado ao mercado de energia",
                "message": "Documento processado mas marcado como irrelevante"
            }
        
        # Criar documento secundário no banco com resultados do workflow
        document = SecondaryDocumentModel(
            filename=file.filename,
            document_type=document_type,
            document_name=document_name,
            presented_by=presented_by,
            presented_at=presented_at,
            summary=workflow_result["summary"],  # Summary contextualizado
            central_theme=workflow_result["central_theme"],
            key_points=workflow_result["key_points"],
            party_affiliation=party_affiliation,
            role=role,
            primary_id=primary_id
        )
        
        db.add(document)
        db.flush()  # Para obter o ID
        
        # Associar subjects identificados pelo workflow
        for subject_name in workflow_result["subjects"]:
            subject = db.query(SubjectModel).filter(SubjectModel.name == subject_name).first()
            if subject:
                document.subjects.append(subject)
        
        # Processar e armazenar chunks no vector store
        splitter = await create_document_processor(primary.collection_name)
        processed_chunks = splitter.process_and_store_document(
            md_text=workflow_result["text_content"], 
            doc_id=document.id, 
            filename=file.filename, 
            document_type=document_type,
            parent_id=primary_id,
            subjects=workflow_result["subjects"]
        )
        
        db.commit()
        
        logger.info(f"Documento secundário {document_name} processado com sucesso")
        
        return {
            "document_name": document_name,
            "document_id": document.id,
            "primary_document": primary.document_name,
            "processing_status": workflow_result["processing_status"],
            "subjects": workflow_result["subjects"],
            "central_theme": workflow_result["central_theme"],
            "key_points": workflow_result["key_points"],
            "relevance_score": workflow_result["relevance_score"],
            "chunks_processed": processed_chunks,
            "message": f"{processed_chunks} chunks indexados na coleção '{primary.collection_name}'"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Cleanup em caso de erro
        if 'document' in locals() and hasattr(document, 'id') and document.id:
            db.rollback()
            try:
                splitter = await create_document_processor(primary.collection_name)
                splitter.delete_document_from_vector_db(document.id)
            except:
                pass  # Falha no cleanup não deve quebrar o erro principal
        
        logger.error(f"Erro ao processar documento secundário {document_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar documento: {str(e)}")

# ==================== ENDPOINTS AUXILIARES ====================

@router.get("/", summary="Lista todos os documentos principais")
def list_primary_documents(db: Session = Depends(get_db_session)):
    documents = db.query(PrimaryDocumentModel).all()
    return [PrimaryDocumentResponse.model_validate(document) for document in documents]

@router.get("/{doc_id}", summary="Lista documento principal e secundários")
async def get_document_with_secondaries(doc_id: int, db: Session = Depends(get_db_session)):
    primary_document = db.query(PrimaryDocumentModel).filter(PrimaryDocumentModel.id == doc_id).first()
    if not primary_document:
        raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' não encontrado")
    
    secondary_documents = db.query(SecondaryDocumentModel).filter(SecondaryDocumentModel.primary_id == doc_id).all()
    
    primary_response = PrimaryDocumentResponse.model_validate(primary_document)
    return SecondaryDocumentListResponse(
        primary_id=primary_document.id, 
        primary=primary_response, 
        secondaries=secondary_documents
    )

@router.delete("/{doc_id}", summary="Remove documento principal e secundários")
async def delete_document(doc_id: int, db: Session = Depends(get_db_session)):
    try:
        # Verificar existência
        primary_document = db.query(PrimaryDocumentModel).filter(PrimaryDocumentModel.id == doc_id).first()
        if not primary_document:
            raise HTTPException(status_code=404, detail=f"Documento '{doc_id}' não encontrado")
        
        secondary_documents = db.query(SecondaryDocumentModel).filter(SecondaryDocumentModel.primary_id == doc_id).all()
        
        # Remover do vector store
        splitter = await create_document_processor(primary_document.collection_name)
        
        try:
            splitter.delete_document_from_vector_db(doc_id)
        except Exception as e:
            logger.error(f"Erro ao remover coleção '{primary_document.collection_name}' do vector store: {str(e)}")
        
        # Remover documentos secundários
        for secondary in secondary_documents:
            try:
                secondary_splitter = await create_document_processor(secondary.collection_name)
                secondary_splitter.delete_document_from_vector_db(secondary.id)
            except Exception as e:
                logger.error(f"Erro ao remover documento secundário {secondary.id}: {str(e)}")
            db.delete(secondary)
        
        # Remover documento principal
        db.delete(primary_document)
        db.commit()
        
        return {
            "doc_id": doc_id,
            "message": f"Documento principal e {len(secondary_documents)} secundários removidos"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao deletar documento {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao deletar documento")