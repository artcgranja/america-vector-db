from typing import Dict, List, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class RelevanceResponse(BaseModel):
    """Schema para resposta do verificador de relevância"""
    is_energy_related: bool = Field(..., description="Se o documento é relacionado ao mercado de energia")
    confidence_score: float = Field(..., description="Score de confiança (0.0 - 1.0)")
    main_reason: str = Field(..., description="Principal razão da classificação")

class RelevanceChecker:
    """
    Verificador de relevância para documentos do mercado de energia.
    Determina se um documento é relacionado ao setor energético brasileiro.
    Seguindo princípio KISS: simples, direto e eficaz.
    """
    
    def __init__(
        self, 
        db_session: Session, 
        model: str = "gemini-2.0-flash-001", 
        temperature: float = 0.1
    ):
        """
        Inicializa o verificador de relevância.
        
        Args:
            db_session: Sessão do banco de dados (para consistência)
            model: Modelo do Google Gemini a ser usado
            temperature: Temperatura para geração (0.0 - 1.0)
        """
        self.db_session = db_session
        
        # Inicializar LLM
        self.llm = ChatGoogleGenerativeAI(
            model=model, 
            temperature=temperature,
            max_output_tokens=200
        )
        
        # Parser para estruturar resposta
        self.parser = PydanticOutputParser(pydantic_object=RelevanceResponse)
        
        # Construir prompt
        self.prompt = self._build_prompt()
        
        # Criar chain
        self.chain = self.prompt | self.llm | self.parser
        
        logger.info("RelevanceChecker inicializado")
    
    def _build_prompt(self) -> ChatPromptTemplate:
        """Constrói o prompt para verificação de relevância"""
        
        system_prompt = """
Você é um especialista em análise de documentos do mercado de energia elétrica brasileiro.
Sua tarefa é determinar se um documento está relacionado ao setor energético.

CONSIDERE RELACIONADO AO MERCADO DE ENERGIA:
- Geração de energia (hidrelétrica, térmica, solar, eólica, biomassa)
- Transmissão e distribuição de energia elétrica
- Comercialização de energia (mercado livre/cativo)
- Tarifas e preços de energia
- Regulamentação do setor elétrico (ANEEL, ONS, CCEE)
- Eficiência energética
- Consumidores de energia
- Agentes do setor elétrico
- Infraestrutura energética
- Políticas energéticas

CONSIDERE NÃO RELACIONADO:
- Assuntos administrativos gerais
- Outros setores (telecomunicações, petróleo, gás)
- Questões processuais sem impacto no setor
- Temas não aplicáveis ao mercado de energia

INSTRUÇÕES:
1. Analise o documento
2. Determine se é relevante para o mercado de energia
3. Atribua um score de confiança (0.0 = certeza que não é, 1.0 = certeza que é)
4. Explique brevemente o motivo da classificação

Responda no formato JSON especificado:
{format_instructions}
"""
        
        human_prompt = """
DOCUMENTO A ANALISAR:
{input}

Análise:"""
        
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            HumanMessagePromptTemplate.from_template(human_prompt),
        ]).partial(format_instructions=self.parser.get_format_instructions())
    
    def check_relevance(self, document_text: str) -> Dict[str, Any]:
        """
        Verifica se um documento é relevante para o mercado de energia.
        
        Args:
            document_text: Texto do documento para analisar
            
        Returns:
            Dict com is_energy_related, confidence_score e main_reason
            
        Raises:
            Exception: Se houver erro na verificação
        """
        try:
            # Validar input básico
            if not document_text or not document_text.strip():
                logger.warning("Documento vazio fornecido para verificação de relevância")
                return {
                    "is_energy_related": False,
                    "confidence_score": 0.0,
                    "main_reason": "Documento vazio"
                }
            
            # Limitar tamanho do texto
            max_chars = 5000  # Suficiente para determinar relevância
            if len(document_text) > max_chars:
                document_text = document_text[:max_chars] + "..."
                logger.info(f"Texto truncado para {max_chars} caracteres")
            
            # Executar verificação
            logger.info("Iniciando verificação de relevância")
            response = self.chain.invoke({"input": document_text})
            
            result = {
                "is_energy_related": response.is_energy_related,
                "confidence_score": response.confidence_score,
                "main_reason": response.main_reason
            }
            
            logger.info(f"Relevância verificada: {response.is_energy_related} (confiança: {response.confidence_score})")
            return result
            
        except Exception as e:
            logger.error(f"Erro na verificação de relevância: {e}")
            raise


# Função de conveniência para usar no workflow
def check_document_relevance(document_text: str, db_session: Session) -> Dict[str, Any]:
    """
    Função de conveniência para verificar relevância de um documento.
    
    Args:
        document_text: Texto do documento
        db_session: Sessão do banco de dados
        
    Returns:
        Dict com resultado da verificação
    """
    checker = RelevanceChecker(db_session)
    return checker.check_relevance(document_text)