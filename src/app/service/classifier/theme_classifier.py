from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class ThemeClassifier:
    """
    Classificador de tema central para documentos do mercado de energia.
    Usa Google Gemini para identificar o tema principal de um documento.
    Seguindo princípio KISS: simples, direto e eficaz.
    """
    
    def __init__(
        self, 
        db_session: Session, 
        model: str = "gemini-2.0-flash-001", 
        temperature: float = 0.1
    ):
        """
        Inicializa o classificador de tema central.
        
        Args:
            db_session: Sessão do banco de dados (para consistência com outros classificadores)
            model: Modelo do Google Gemini a ser usado
            temperature: Temperatura para geração (0.0 - 1.0)
        """
        self.db_session = db_session
        
        # Inicializar LLM
        self.llm = ChatGoogleGenerativeAI(
            model=model, 
            temperature=temperature,
            max_output_tokens=100  # Tema central deve ser conciso
        )
        
        # Construir prompt
        self.prompt = self._build_prompt()
        
        # Criar chain
        self.chain = self.prompt | self.llm
        
        logger.info("ThemeClassifier inicializado")
    
    def _build_prompt(self) -> ChatPromptTemplate:
        """Constrói o prompt para classificação de tema central"""
        
        system_prompt = """
Você é um especialista em análise de documentos do mercado de energia elétrica brasileiro.
Sua tarefa é identificar o TEMA CENTRAL de um documento em uma frase clara e objetiva.

INSTRUÇÕES:
1. Leia o documento fornecido
2. Identifique o assunto PRINCIPAL que o documento aborda
3. Responda com UMA FRASE que resuma o tema central
4. Seja específico e direto
5. Use linguagem técnica apropriada do setor energético
6. Máximo de 15 palavras

EXEMPLOS DE BONS TEMAS CENTRAIS:
- "Marco regulatório para energia solar distribuída"
- "Alteração nas regras de compensação energética"
- "Nova metodologia tarifária para distribuidoras"
- "Regulamentação de comercializadores de energia"

Responda APENAS com o tema central, sem explicações adicionais.
"""
        
        human_prompt = """
DOCUMENTO:
{input}

TEMA CENTRAL:"""
        
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            HumanMessagePromptTemplate.from_template(human_prompt),
        ])
    
    def classify_theme(self, document_text: str) -> str:
        """
        Identifica o tema central de um documento.
        
        Args:
            document_text: Texto do documento para analisar
            
        Returns:
            String com o tema central identificado
            
        Raises:
            Exception: Se houver erro na classificação
        """
        try:
            # Validar input básico
            if not document_text or not document_text.strip():
                logger.warning("Documento vazio fornecido para classificação de tema")
                return ""
            
            # Limitar tamanho do texto
            max_chars = 6000  # Menor que subjects pois tema é mais simples
            if len(document_text) > max_chars:
                document_text = document_text[:max_chars] + "..."
                logger.info(f"Texto truncado para {max_chars} caracteres")
            
            # Executar classificação
            logger.info("Iniciando classificação de tema central")
            response = self.chain.invoke({"input": document_text})
            
            # Limpar e validar resposta
            theme = response.content.strip()
            
            # Remover aspas se existirem
            if theme.startswith('"') and theme.endswith('"'):
                theme = theme[1:-1]
            
            logger.info(f"Tema central identificado: {theme}")
            return theme
            
        except Exception as e:
            logger.error(f"Erro na classificação de tema central: {e}")
            raise


# Função de conveniência para usar no workflow
def classify_central_theme(document_text: str, db_session: Session) -> str:
    """
    Função de conveniência para classificar tema central de um documento.
    
    Args:
        document_text: Texto do documento
        db_session: Sessão do banco de dados
        
    Returns:
        Tema central identificado
    """
    classifier = ThemeClassifier(db_session)
    return classifier.classify_theme(document_text)