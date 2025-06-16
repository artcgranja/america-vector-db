from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain_core.output_parsers import PydanticOutputParser
from sqlalchemy.orm import Session
from src.app.db.models.subjects import SubjectModel
from src.app.schemas.classifier_schemas import ClassifierResponse
import json
import logging

logger = logging.getLogger(__name__)

class SubjectsClassifier:
    """
    Classificador de assuntos para documentos do mercado de energia.
    Usa Google Gemini para identificar subjects relevantes baseados em uma lista pré-definida.
    """
    
    def __init__(
        self, 
        db_session: Session, 
        model: str = "gemini-2.0-flash-001", 
        temperature: float = 0.1,
        max_subjects: int = 10
    ):
        """
        Inicializa o classificador de subjects.
        
        Args:
            db_session: Sessão do banco de dados
            model: Modelo do Google Gemini a ser usado
            temperature: Temperatura para geração (0.0 - 1.0)
            max_subjects: Número máximo de subjects a retornar
        """
        self.db_session = db_session
        self.max_subjects = max_subjects
        
        # Inicializar LLM
        self.llm = ChatGoogleGenerativeAI(
            model=model, 
            temperature=temperature,
            max_output_tokens=1000
        )
        
        # Parser para estruturar a resposta
        self.parser = PydanticOutputParser(pydantic_object=ClassifierResponse)
        
        # Carregar subjects disponíveis do banco
        self.available_subjects = self._load_subjects_from_db()
        
        # Construir prompt
        self.prompt = self._build_prompt()
        
        # Criar chain
        self.chain = self.prompt | self.llm | self.parser
        
        logger.info(f"SubjectsClassifier inicializado com {len(self.available_subjects)} subjects")
    
    def _load_subjects_from_db(self) -> List[str]:
        """Carrega lista de subjects disponíveis do banco de dados"""
        try:
            subjects = self.db_session.query(SubjectModel).all()
            subjects_list = [subject.name for subject in subjects]
            
            if not subjects_list:
                logger.warning("Nenhum subject encontrado no banco de dados")
                return []
                
            logger.info(f"Carregados {len(subjects_list)} subjects do banco")
            return subjects_list
            
        except Exception as e:
            logger.error(f"Erro ao carregar subjects do banco: {e}")
            return []
    
    def _build_prompt(self) -> ChatPromptTemplate:
        """Constrói o prompt para classificação"""
        
        system_prompt = """
Você é um especialista em análise de documentos do mercado de energia elétrica brasileiro.
Sua tarefa é identificar os principais assuntos (subjects) que um documento aborda.

INSTRUÇÕES:
1. Analise cuidadosamente o texto fornecido
2. Identifique os temas principais relacionados ao mercado de energia
3. Selecione APENAS os subjects da lista fornecida que são REALMENTE relevantes
4. Retorne no máximo {max_subjects} subjects
5. Ordene por relevância (mais relevante primeiro)
6. Seja preciso - prefira menos subjects bem escolhidos do que muitos pouco relevantes

SUBJECTS DISPONÍVEIS:
{subjects_list}

CRITÉRIOS PARA SELEÇÃO:
- O subject deve estar diretamente relacionado ao conteúdo principal
- Evite subjects muito genéricos se existirem opções mais específicas
- Considere tanto temas principais quanto secundários importantes
- Foque nos aspectos que teriam maior impacto no mercado de energia

Responda APENAS no formato JSON especificado abaixo:
{format_instructions}
"""
        
        human_prompt = """
DOCUMENTO A ANALISAR:
{input}

Baseado na análise do documento acima, identifique os subjects mais relevantes da lista fornecida.
"""
        
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            HumanMessagePromptTemplate.from_template(human_prompt),
        ]).partial(
            format_instructions=self.parser.get_format_instructions(),
            subjects_list=json.dumps(self.available_subjects, ensure_ascii=False, indent=2),
            max_subjects=self.max_subjects
        )
    
    def classify_document(self, document_text: str) -> List[str]:
        """
        Classifica um documento e retorna lista de subjects relevantes.
        
        Args:
            document_text: Texto do documento para classificar
            
        Returns:
            Lista de subjects identificados
            
        Raises:
            Exception: Se houver erro na classificação
        """
        try:
            # Validar input
            if not document_text or not document_text.strip():
                logger.warning("Documento vazio fornecido para classificação")
                return []
            
            if not self.available_subjects:
                logger.error("Nenhum subject disponível para classificação")
                return []
            
            # Limitar tamanho do texto se necessário (evitar tokens excessivos)
            max_chars = 8000  # Aproximadamente 2000 tokens
            if len(document_text) > max_chars:
                document_text = document_text[:max_chars] + "..."
                logger.info(f"Texto truncado para {max_chars} caracteres")
            
            # Executar classificação
            logger.info("Iniciando classificação de subjects")
            response = self.chain.invoke({"input": document_text})
            
            logger.info(f"Classificação concluída: {len(response.subjects)} subjects identificados")
            return response.subjects
            
        except Exception as e:
            logger.error(f"Erro na classificação de subjects: {e}")
            raise
    

    
    def get_available_subjects(self) -> List[str]:
        """Retorna lista de subjects disponíveis"""
        return self.available_subjects.copy()
    
    def refresh_subjects(self) -> None:
        """Recarrega subjects do banco de dados"""
        logger.info("Recarregando subjects do banco de dados")
        self.available_subjects = self._load_subjects_from_db()
        self.prompt = self._build_prompt()
        self.chain = self.prompt | self.llm | self.parser


# Função de conveniência para usar no workflow
def classify_document_subjects(
    document_text: str,
    db_session: Session,
    max_subjects: int = 10
) -> List[str]:
    """
    Função de conveniência para classificar subjects de um documento.
    
    Args:
        document_text: Texto do documento
        db_session: Sessão do banco de dados
        max_subjects: Número máximo de subjects
        
    Returns:
        Lista de subjects classificados
    """
    classifier = SubjectsClassifier(db_session, max_subjects=max_subjects)
    return classifier.classify_document(document_text)