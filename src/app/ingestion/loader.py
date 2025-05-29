import tempfile
from typing import List
from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader
from langchain.schema import Document

async def load_document(file: UploadFile) -> List[Document]:
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

    return documents