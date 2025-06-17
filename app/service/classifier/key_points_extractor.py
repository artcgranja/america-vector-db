from typing import Dict, Any
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

class KeyPointsResponse(BaseModel):
    """Schema para resposta dos pontos-chave"""
    key_points: Dict[str, str] = Field(
        ..., 
        description="Dicionário com tópico como chave e descrição como valor"
    )

class KeyPointsExtractor:
    """
    Extrator de pontos-chave para documentos do mercado de energia.
    Identifica os principais tópicos e suas descrições de forma simples.
    Seguindo princípio KISS: simples, direto e eficaz.
    """
    
    def __init__(
        self, 
        db_session: Session, 
        model: str = "gemini-2.0-flash-001", 
        temperature: float = 0.1
    ):
        """
        Inicializa o extrator de pontos-chave.
        
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
            max_output_tokens=800
        )
        
        # Parser para estruturar resposta
        self.parser = PydanticOutputParser(pydantic_object=KeyPointsResponse)
        
        # Construir prompt
        self.prompt = self._build_prompt()
        
        # Criar chain
        self.chain = self.prompt | self.llm | self.parser
        
        logger.info("KeyPointsExtractor inicializado")
    
    def _build_prompt(self) -> ChatPromptTemplate:
        """Constrói o prompt para extração de pontos-chave"""
        
        system_prompt = """
Você é um especialista em análise de documentos do mercado de energia elétrica brasileiro.
Sua tarefa é extrair os pontos-chave mais importantes de um documento.

INSTRUÇÕES:
1. Identifique os 3-6 pontos mais importantes do documento
2. Para cada ponto, crie um tópico conciso e uma descrição clara
3. Foque no que realmente importa para o mercado de energia
4. Use linguagem técnica apropriada mas acessível
5. Seja objetivo e direto

FORMATO DE SAÍDA:
- Tópico: frase curta (máximo 5 palavras)
- Descrição: explicação clara do que o documento diz sobre esse tópico

EXEMPLOS DE BONS PONTOS-CHAVE:
- "Marco Regulatório": "Estabelece novas regras para energia solar distribuída com limite de 5MW"
- "Tarifas": "Cria nova modalidade tarifária para prosumidores com desconto de 30%"
- "Prazo de Adequação": "Distribuidoras têm 12 meses para implementar as mudanças"

Responda no formato JSON especificado:
{format_instructions}
"""
        
        human_prompt = """
DOCUMENTO PARA ANÁLISE:
{input}

Pontos-chave:"""
        
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            HumanMessagePromptTemplate.from_template(human_prompt),
        ]).partial(format_instructions=self.parser.get_format_instructions())
    
    def extract_key_points(self, document_text: str) -> Dict[str, str]:
        """
        Extrai os pontos-chave de um documento.
        
        Args:
            document_text: Texto do documento para analisar
            
        Returns:
            Dict com tópicos como chaves e descrições como valores
            
        Raises:
            Exception: Se houver erro na extração
        """
        try:
            # Validar input básico
            if not document_text or not document_text.strip():
                logger.warning("Documento vazio fornecido para extração de pontos-chave")
                return {}
            
            # Limitar tamanho do texto
            max_chars = 7000  # Suficiente para identificar pontos principais
            if len(document_text) > max_chars:
                document_text = document_text[:max_chars] + "..."
                logger.info(f"Texto truncado para {max_chars} caracteres")
            
            # Executar extração
            logger.info("Iniciando extração de pontos-chave")
            response = self.chain.invoke({"input": document_text})
            
            key_points = response.key_points
            
            logger.info(f"Extração concluída: {len(key_points)} pontos-chave identificados")
            return key_points
            
        except Exception as e:
            logger.error(f"Erro na extração de pontos-chave: {e}")
            raise


# Função de conveniência para usar no workflow
def extract_document_key_points(document_text: str, db_session: Session) -> Dict[str, str]:
    """
    Função de conveniência para extrair pontos-chave de um documento.
    
    Args:
        document_text: Texto do documento
        db_session: Sessão do banco de dados
        
    Returns:
        Dict com pontos-chave extraídos
    """
    extractor = KeyPointsExtractor(db_session)
    return extractor.extract_key_points(document_text)