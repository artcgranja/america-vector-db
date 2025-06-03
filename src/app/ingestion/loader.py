import tempfile
from typing import List, Dict
from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader
from langchain.schema import Document
from datetime import datetime

class DocumentMetadata:
    def __init__(self, document_type: str, parent_id: str = None):
        self.document_type = document_type
        self.parent_id = parent_id
        self.hierarchy_level = 0 if parent_id is None else 1
        self.timestamp = datetime.now().isoformat()
        
    def to_dict(self) -> Dict:
        return {
            "document_type": self.document_type,
            "parent_id": self.parent_id,
            "hierarchy_level": self.hierarchy_level,
            "timestamp": self.timestamp
        }

async def load_document(file: UploadFile, document_type: str, parent_id: str = None) -> List[Document]:
    """
    Carrega um arquivo de upload (PDF ou TXT) e retorna uma lista de objetos Document do LangChain.
    """
    filename = file.filename.lower()

    # PDF
    if filename.endswith(".pdf"):
        # Ler conteúdo do upload
        contents = await file.read()
        # Salvar em arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        # Carregar PDF usando PyPDFLoader
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()

    # TXT
    elif filename.endswith(".txt"):
        contents = (await file.read()).decode("utf-8")
        documents = [
            Document(
                page_content=contents,
                metadata={"source": file.filename}
            )
        ]

    else:
        raise ValueError(f"Formato de arquivo não suportado: {file.filename}")

    # Enhance metadata
    metadata = DocumentMetadata(document_type, parent_id).to_dict()
    metadata.update({
        "source": file.filename,
        "file_size": len(contents),
        "mime_type": file.content_type
    })
    
    return [Document(page_content=content, metadata=metadata) for content in documents]