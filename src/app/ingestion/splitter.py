from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.config import settings

def split_document(documents: List[Document]) -> List[Document]:
    """
    Divide uma lista de Document em chunks menores usando parâmetros do settings.

    Args:
        documents: Lista de Document carregados pelo loader.

    Returns:
        Lista de Document subdivididos em chunks de tamanho definido em settings.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    return splitter.split_documents(documents)