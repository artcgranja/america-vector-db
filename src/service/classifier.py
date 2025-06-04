from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain_core.output_parsers import PydanticOutputParser
from src.app.schemas.classifier_schemas import ClassifierResponse, EnergySubjectEnum
from src.service.promt import SYSTEM_PROMPT
import json

class ClassifierModel:
    def __init__(self, model: str = "gemini-2.0-flash-001", temperature: float = 0.1):
        self.llm = ChatGoogleGenerativeAI(model=model, temperature=temperature)
        
        self.parser = PydanticOutputParser(pydantic_object=ClassifierResponse)
        
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
            HumanMessagePromptTemplate.from_template("{input}"),
        ]).partial(format_instructions=self.parser.get_format_instructions())
        self.chain = self.prompt | self.llm | self.parser

    def classify_markdown_file(self, markdown_text: str) -> ClassifierResponse:
        """
        Processa um arquivo markdown e retorna sua classificação.

        Args:
            markdown_text: Texto markdown para classificar

        Returns:
            ClassifierResponse: Resposta com a classificação do documento
        """
        try:
            response = self.chain.invoke({"input": markdown_text})
            return response.subjects

        except Exception as e:
            print(f"Erro ao classificar arquivo: {e}")
            raise

classifier = ClassifierModel()