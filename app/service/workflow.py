from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.db.models.documents import PrimaryDocumentModel
from app.service.summarization.summaryzer import SummaryzerModel
from app.service.classifier.subjects_classifier import SubjectsClassifier
from app.service.classifier.theme_classifier import ThemeClassifier
from app.ingestion.convertor import converter


class DocumentProcessingState(TypedDict):
    """Estado do workflow de processamento de documentos"""
    
    # Input inicial
    file: UploadFile
    filename: str
    db_session: Session
    
    # Processamento
    text_content: str
    document_type: str  # "primary" ou "secondary"
    primary_id: Optional[int]  # ID do documento principal (para secundários)
    primary_context: Optional[str]  # Contexto do documento principal
    
    # Resultados da análise
    summary: str
    is_energy_related: bool
    relevance_score: float
    irrelevance_reasons: List[str]
    
    # Classificações
    subjects: List[str]
    central_theme: str
    key_points: Dict[str, str]
    
    # Output
    document_id: Optional[int]
    chunks_processed: int
    processing_status: str  # "success", "irrelevant", "error"
    error_message: Optional[str]


class DocumentProcessingWorkflow:
    """Workflow principal para processamento de documentos"""
    
    def __init__(self):
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Constrói o grafo do workflow"""
        
        # Criar o grafo
        workflow = StateGraph(DocumentProcessingState)
        
        # Adicionar nós
        workflow.add_node("convert_to_text", self.convert_to_text_node)
        workflow.add_node("check_document_type", self.check_document_type_node)
        workflow.add_node("get_primary_context", self.get_primary_context_node)
        workflow.add_node("summarize", self.summarize_node)
        workflow.add_node("contextualized_summarize", self.contextualized_summarize_node)
        workflow.add_node("check_relevance", self.check_relevance_node)
        workflow.add_node("classify_subjects", self.classify_subjects_node)
        workflow.add_node("classify_theme", self.classify_theme_node)
        workflow.add_node("extract_key_points", self.extract_key_points_node)
        workflow.add_node("combine_results", self.combine_results_node)
        workflow.add_node("mark_irrelevant", self.mark_irrelevant_node)
        workflow.add_node("store_document", self.store_document_node)
        
        # Definir entrada
        workflow.set_entry_point("convert_to_text")
        
        # Definir fluxo
        workflow.add_edge("convert_to_text", "check_document_type")
        
        # Fluxo condicional baseado no tipo de documento
        workflow.add_conditional_edges(
            "check_document_type",
            self.route_by_document_type,
            {
                "primary": "summarize",
                "secondary": "get_primary_context"
            }
        )
        
        # Fluxo dos documentos secundários
        workflow.add_edge("get_primary_context", "contextualized_summarize")
        workflow.add_edge("contextualized_summarize", "check_relevance")
        
        # Fluxo dos documentos principais
        workflow.add_edge("summarize", "check_relevance")
        
        # Fluxo condicional de relevância
        workflow.add_conditional_edges(
            "check_relevance",
            self.route_by_relevance,
            {
                "relevant": "classify_subjects",
                "irrelevant": "mark_irrelevant"
            }
        )
        
        # Classificações sequenciais (podem ser paralelizadas no futuro)
        workflow.add_edge("classify_subjects", "classify_theme")
        workflow.add_edge("classify_theme", "extract_key_points")
        workflow.add_edge("extract_key_points", "combine_results")
        
        # Convergência
        workflow.add_edge("mark_irrelevant", "combine_results")
        workflow.add_edge("combine_results", "store_document")
        workflow.add_edge("store_document", END)
        
        return workflow.compile()
    
    # ==================== NÔES DO WORKFLOW ====================
    
    async def convert_to_text_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Converte o arquivo para texto"""
        try:
            state["text_content"] = await converter.convert_file(state["file"], state["filename"])
            return state
        except Exception as e:
            state["processing_status"] = "error"
            state["error_message"] = f"Erro na conversão: {str(e)}"
            return state
    
    def check_document_type_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Verifica se é documento principal ou secundário"""
        return state
    
    def get_primary_context_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Busca contexto do documento principal para documentos secundários"""
        try:
            # Assumindo que documento principal é sempre MPV por enquanto
            # Isso pode ser generalizado futuramente
            primary_doc = state["db_session"].query(PrimaryDocumentModel).filter(
                PrimaryDocumentModel.id == state["primary_id"]
            ).first()
            
            if primary_doc:
                state["primary_context"] = primary_doc.summary
            else:
                state["primary_context"] = None
                
            return state
        except Exception as e:
            state["processing_status"] = "error"
            state["error_message"] = f"Erro ao buscar contexto do documento principal: {str(e)}"
            return state
    
    def summarize_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Gera resumo para documentos principais"""
        try:
            summarizer = SummaryzerModel(state["db_session"])
            state["summary"] = summarizer.summarize_markdown_file(state["text_content"])
            return state
        except Exception as e:
            state["processing_status"] = "error"
            state["error_message"] = f"Erro na sumarização: {str(e)}"
            return state
    
    def contextualized_summarize_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Gera resumo contextualizado para documentos secundários"""
        try:
            summarizer = SummaryzerModel(state["db_session"])
            state["summary"] = summarizer.summarize_markdown_file(
                state["text_content"], 
                state["primary_context"]
            )
            return state
        except Exception as e:
            state["processing_status"] = "error"
            state["error_message"] = f"Erro na sumarização contextualizada: {str(e)}"
            return state
    
    def check_relevance_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Verifica se o documento é relevante para o mercado de energia"""
        try:
            from app.service.classifier.relevance_checker import RelevanceChecker
            
            checker = RelevanceChecker(state["db_session"])
            result = checker.check_relevance(state["summary"])
            
            state["is_energy_related"] = result["is_energy_related"]
            state["relevance_score"] = result["confidence_score"]
            state["irrelevance_reasons"] = [result["main_reason"]] if not result["is_energy_related"] else []
            
            return state
        except Exception as e:
            state["processing_status"] = "error"
            state["error_message"] = f"Erro na verificação de relevância: {str(e)}"
            return state
    
    def classify_subjects_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Classifica os assuntos do documento"""
        try:
            classifier = SubjectsClassifier(state["db_session"])
            state["subjects"] = classifier.classify_document(state["summary"])
            return state
        except Exception as e:
            state["processing_status"] = "error"
            state["error_message"] = f"Erro na classificação de assuntos: {str(e)}"
            return state
    
    def classify_theme_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Classifica o tema central do documento"""
        try:
            classifier = ThemeClassifier(state["db_session"])
            state["central_theme"] = classifier.classify_theme(state["summary"])
            return state
        except Exception as e:
            state["processing_status"] = "error"
            state["error_message"] = f"Erro na classificação de tema: {str(e)}"
            return state
    
    def extract_key_points_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Extrai pontos principais em formato JSON"""
        try:
            from app.service.classifier.key_points_extractor import KeyPointsExtractor
            
            extractor = KeyPointsExtractor(state["db_session"])
            state["key_points"] = extractor.extract_key_points(state["summary"])
            
            return state
        except Exception as e:
            state["processing_status"] = "error"
            state["error_message"] = f"Erro na extração de pontos-chave: {str(e)}"
            return state
    
    def combine_results_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Combina todos os resultados"""
        if state["processing_status"] != "error":
            if state["is_energy_related"]:
                state["processing_status"] = "success"
            else:
                state["processing_status"] = "irrelevant"
        return state
    
    def mark_irrelevant_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Marca documento como irrelevante"""
        state["processing_status"] = "irrelevant"
        state["subjects"] = []
        state["central_theme"] = ""
        state["key_points"] = {}
        return state
    
    def store_document_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Armazena o documento no banco de dados"""
        # TODO: Implementar armazenamento no banco
        state["document_id"] = 999  # Placeholder
        state["chunks_processed"] = 0  # Placeholder
        return state
    
    # ==================== FUNÇÕES DE ROTEAMENTO ====================
    
    def route_by_document_type(self, state: DocumentProcessingState) -> str:
        """Roteia baseado no tipo de documento"""
        return "primary" if state["document_type"] == "primary" else "secondary"
    
    def route_by_relevance(self, state: DocumentProcessingState) -> str:
        """Roteia baseado na relevância do documento"""
        return "relevant" if state["is_energy_related"] else "irrelevant"
    
    # ==================== FUNÇÃO PRINCIPAL ====================
    
    async def process_document(
        self,
        file: UploadFile,
        filename: str,
        db_session: Session,
        primary_id: int = None
    ) -> DocumentProcessingState:
        """
        Processa um documento através do workflow completo
        
        Args:
            file: Arquivo uploaded
            filename: Nome do arquivo
            primary_id: ID do documento principal (para documentos secundários)
            db_session: Sessão do banco de dados
            
        Returns:
            Estado final do processamento
        """
        
        # Estado inicial
        initial_state: DocumentProcessingState = {
            "file": file,
            "filename": filename,
            "db_session": db_session,
            "text_content": "",
            "document_type": "",
            "primary_id": primary_id,
            "primary_context": None,
            "summary": "",
            "is_energy_related": False,
            "relevance_score": 0.0,
            "irrelevance_reasons": [],
            "subjects": [],
            "central_theme": "",
            "key_points": {},
            "document_id": None,
            "chunks_processed": 0,
            "processing_status": "",
            "error_message": None
        }
        
        # Executar workflow
        try:
            if primary_id:
                initial_state["document_type"] = "secondary"
            else:
                initial_state["document_type"] = "primary"

            final_state = await self.workflow.ainvoke(initial_state)
            return final_state
        except Exception as e:
            initial_state["processing_status"] = "error"
            initial_state["error_message"] = f"Erro no workflow: {str(e)}"
            return initial_state


# ==================== INSTÂNCIA GLOBAL ====================

# Instância única do workflow para ser usada nos endpoints
document_workflow = DocumentProcessingWorkflow()