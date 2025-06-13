from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from src.app.service.promt import SUMMARY_PROMPT_SYSTEM
from sqlalchemy.orm import Session
import json

class SummaryzerModel:
    def __init__(self, db: Session, model: str = "gemini-2.0-flash-001", temperature: float = 0.1):
        self.llm = ChatGoogleGenerativeAI(model=model, temperature=temperature)
        self.db = db
        
        # Template base sem contexto
        self.base_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(SUMMARY_PROMPT_SYSTEM),
            HumanMessagePromptTemplate.from_template("{input}"),
        ])
        
        # Template com contexto
        self.context_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(SUMMARY_PROMPT_SYSTEM),
            HumanMessagePromptTemplate.from_template("{input}"),
            HumanMessagePromptTemplate.from_template("{context}"),
        ])
        
    def summarize_markdown_file(self, markdown_text: str, mpv_summary: str | None = None) -> str:
        try:
            if mpv_summary:
                chain = self.context_prompt | self.llm
                response = chain.invoke({"input": markdown_text, "context": mpv_summary})
            else:
                chain = self.base_prompt | self.llm
                response = chain.invoke({"input": markdown_text})
            
            return response.content

        except Exception as e:
            print(f"Erro ao resumir arquivo: {e}")
            raise